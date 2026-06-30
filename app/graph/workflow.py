"""
LangGraph 多 Agent 工作流 - 支持动态路由 + 并行执行
"""
from typing import TypedDict, Annotated, Literal, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from app.agents.planner_agent import planner_agent
from app.agents.attraction_agent import attraction_agent
from app.agents.weather_agent import weather_agent
from app.agents.hotel_agent import hotel_agent
from app.models.llm_client import llm_client
from app.utils.prompt_templates import PLANNER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


# 路由决策的结构化输出 Schema（Pydantic 自动生成 JSON Schema）
class RoutingDecision(BaseModel):
    """LLM 路由决策的结构化输出模型，通过 function calling 强制校验"""
    agents: List[Literal["attraction", "weather", "hotel"]] = Field(
        description="需要运行的 Agent 列表，仅从 attraction/weather/hotel 中选取"
    )
    reason: str = Field(
        description="路由决策的简要原因"
    )


# 定义状态
class AgentState(TypedDict):
    """Agent 工作流状态"""
    query: str
    location: str
    days: int
    budget: str
    preferences: str
    
    # 各 Agent 输出
    attraction_result: dict
    weather_result: dict
    hotel_result: dict
    plan_result: dict
    
    # 控制流
    next_step: str
    needs_clarification: bool
    clarification_questions: list
    
    # 动态路由：需要运行的 Agent 列表
    agents_to_run: List[str]  # ['attraction', 'weather', 'hotel']
    completed_agents: List[str]  # 已完成的 Agent
    
    # 最终输出
    final_response: str


# 节点函数
async def router_node(state: AgentState) -> AgentState:
    """
    智能路由节点：根据用户需求决定运行哪些 Agent
    """
    logger.info("Executing router node - deciding which agents to run")
    
    query = state['query']
    location = state['location']
    preferences = state['preferences']
    
    # 构建系统提示
    system_prompt = """你是一个智能路由助手，负责分析用户的旅游需求，决定需要调用哪些专业服务。

可用的 Agent 服务：
1. **attraction** (景点推荐): 当用户询问景点、旅游景点、游玩地点、观光等时使用
2. **weather** (天气查询): 当用户关心天气、气候、是否需要带伞/穿衣建议等时使用
3. **hotel** (酒店推荐): 当用户询问住宿、酒店、旅馆、民宿等时使用

判断规则（严格遵守，不要过度推断）：
- 只包含用户**明确提到或强烈暗示**的 Agent
- 用户只问天气 → 只有 weather，不要加 attraction 或 hotel
- 用户只问景点 → 只有 attraction，不要加 hotel
- 用户只问酒店 → 只有 hotel，不要加 attraction
- 只有用户明确说"旅行规划"、"行程安排"、"玩N天"等完整规划需求时，才同时选多个 Agent

请以 JSON 格式返回，例如：
{"agents": ["weather"], "reason": "用户只询问了天气情况"}
"""
    
    human_message = f"""
用户需求分析：
- 查询: {query}
- 地点: {location}
- 偏好: {preferences}

请决定需要运行哪些 Agent？
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        # 通过 with_structured_output 绑定 Schema，LLM 输出会被强制校验为 RoutingDecision
        structured_llm = llm_client.chat_model.with_structured_output(RoutingDecision)
        
        routing_decision: RoutingDecision = await structured_llm.ainvoke(messages)
        
        # Pydantic 已自动校验类型和枚举值，直接取值
        agents_to_run = routing_decision.agents
        reason = routing_decision.reason
        
        logger.info(f"Routing decision: {agents_to_run}, Reason: {reason}")
        
    except Exception as e:
        logger.error(f"Router node error: {e}, using default agents")
        # 出错时使用默认策略：运行所有 Agent
        agents_to_run = ['attraction', 'weather', 'hotel']
    
    # 确保至少有一个 Agent
    if not agents_to_run:
        agents_to_run = ['attraction']
    
    state['agents_to_run'] = agents_to_run
    state['completed_agents'] = []
    state['next_step'] = agents_to_run[0] if agents_to_run else 'planner'
    
    return state


async def _run_single_agent(agent_name: str, state: AgentState) -> tuple:
    """
    执行单个 Agent，返回 (agent_name, result)
    用于并行调度，各 Agent 之间无数据依赖
    """
    try:
        if agent_name == 'attraction':
            result = await attraction_agent.execute({
                'query': state['query'],
                'location': state['location'],
                'preferences': state['preferences'],
                'budget': state['budget']
            })
        elif agent_name == 'weather':
            result = await weather_agent.execute({
                'location': state['location']
            })
        elif agent_name == 'hotel':
            result = await hotel_agent.execute({
                'location': state['location'],
                'budget': state['budget'],
                'preferences': state['preferences']
            })
        else:
            result = {'error': f'Unknown agent: {agent_name}'}
        
        logger.info(f"Agent [{agent_name}] completed successfully")
        return (agent_name, result)
    except Exception as e:
        logger.error(f"Agent [{agent_name}] failed: {e}")
        return (agent_name, {'error': str(e), 'status': 'failed'})


async def parallel_agents_node(state: AgentState) -> AgentState:
    """
    并行执行节点：同时运行所有路由选中的 Agent
    各 Agent 通过统一输入（城市、预算）独立工作，无跨 Agent 数据依赖
    """
    agents_to_run = state['agents_to_run']
    logger.info(f"Parallel executing agents: {agents_to_run}")
    
    # 并行调度所有 Agent
    tasks = [_run_single_agent(name, state) for name in agents_to_run]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 收集结果到 state
    for item in results:
        if isinstance(item, Exception):
            logger.error(f"Unexpected gather error: {item}")
            continue
        agent_name, result = item
        state[f'{agent_name}_result'] = result
    
    state['completed_agents'] = list(agents_to_run)
    state['next_step'] = 'planner'
    
    logger.info(f"All agents completed, proceeding to planner")
    return state


async def planner_node(state: AgentState) -> AgentState:
    """行程规划节点"""
    logger.info("Executing planner node")

    # 优化：如果只有一个 Agent 且是简单查询，直接返回该 Agent 的结果
    if len(state['agents_to_run']) == 1:
        agent_name = state['agents_to_run'][0]
        agent_result = state.get(f'{agent_name}_result', {})
        
        # 如果有 recommendation 或 suggestion，直接使用
        if 'recommendation' in agent_result:
            state['final_response'] = agent_result['recommendation']
            state['plan_result'] = {'itinerary': agent_result['recommendation']}
            logger.info(f"Single agent mode, using {agent_name} result directly")
            return state
        elif 'suggestion' in agent_result:
            state['final_response'] = agent_result['suggestion']
            state['plan_result'] = {'itinerary': agent_result['suggestion']}
            logger.info(f"Single agent mode, using {agent_name} suggestion directly")
            return state

    # 直接从 state 中取已收集的子 Agent 结果，不重复调用
    attraction_info = state.get('attraction_result', {}).get('recommendation', '')
    weather_info = state.get('weather_result', {}).get('suggestion', '')
    hotel_info = state.get('hotel_result', {}).get('recommendation', '')

    prompt = planner_agent._create_prompt(
        PLANNER_PROMPT,
        query=state['query'],
        location=state['location'],
        days=state['days'],
        budget=state['budget'],
        preferences=state['preferences'],
        attractions=attraction_info,
        weather=weather_info,
        hotels=hotel_info
    )

    itinerary = await planner_agent._call_llm(prompt, cache_key=None)

    state['plan_result'] = {'itinerary': itinerary}
    state['final_response'] = itinerary

    return state


# 构建工作流
def create_workflow():
    """创建 LangGraph 工作流 - 动态路由 + 并行执行"""
    workflow = StateGraph(AgentState)
    
    # 添加节点：router → parallel_agents → planner
    workflow.add_node("router", router_node)
    workflow.add_node("parallel_agents", parallel_agents_node)
    workflow.add_node("planner", planner_node)
    
    # 设置入口点
    workflow.set_entry_point("router")
    
    # router 决策完毕后，统一进入并行执行节点
    workflow.add_edge("router", "parallel_agents")
    
    # 并行执行完毕后，进入规划节点
    workflow.add_edge("parallel_agents", "planner")
    
    # Planner 结束后结束工作流
    workflow.add_edge("planner", END)
    
    # 编译
    app = workflow.compile()
    
    logger.info("Parallel LangGraph workflow created successfully")
    
    return app


# 全局工作流实例
workflow_app = create_workflow()
