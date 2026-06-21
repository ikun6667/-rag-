"""
LangGraph 多 Agent 工作流 - 支持动态路由
"""
from typing import TypedDict, Annotated, Literal, List, Optional
from langgraph.graph import StateGraph, END
from app.agents.planner_agent import planner_agent
from app.agents.attraction_agent import attraction_agent
from app.agents.weather_agent import weather_agent
from app.agents.hotel_agent import hotel_agent
from app.models.llm_client import llm_client
from app.utils.prompt_templates import PLANNER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
import json
import logging

logger = logging.getLogger(__name__)


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
    
    try:
        # 调用 LLM 进行路由决策
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        response = await llm_client.chat_model.ainvoke(messages)
        result_text = response.content
        
        # 解析 JSON 结果
        if '{' in result_text and '}' in result_text:
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            json_str = result_text[start_idx:end_idx]
            routing_decision = json.loads(json_str)
            
            agents_to_run = routing_decision.get('agents', ['attraction', 'weather', 'hotel'])
            reason = routing_decision.get('reason', '')
            
            logger.info(f"Routing decision: {agents_to_run}, Reason: {reason}")
        else:
            # 解析失败，使用默认策略
            logger.warning("Failed to parse routing decision, using default")
            agents_to_run = ['attraction', 'weather', 'hotel']
        
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


async def dynamic_agent_node(state: AgentState, agent_name: str) -> AgentState:
    """
    动态 Agent 执行节点
    
    Args:
        state: 当前状态
        agent_name: 要执行的 Agent 名称
    """
    logger.info(f"Executing dynamic agent node: {agent_name}")
    
    try:
        if agent_name == 'attraction':
            result = await attraction_agent.execute({
                'query': state['query'],
                'location': state['location'],
                'preferences': state['preferences'],
                'budget': state['budget']
            })
            state['attraction_result'] = result
            
        elif agent_name == 'weather':
            result = await weather_agent.execute({
                'location': state['location']
            })
            state['weather_result'] = result
            
        elif agent_name == 'hotel':
            result = await hotel_agent.execute({
                'location': state['location'],
                'budget': state['budget'],
                'preferences': state['preferences']
            })
            state['hotel_result'] = result
        
        # 标记该 Agent 已完成
        if agent_name not in state['completed_agents']:
            state['completed_agents'].append(agent_name)
        
        # 确定下一个要执行的 Agent
        remaining_agents = [a for a in state['agents_to_run'] if a not in state['completed_agents']]
        if remaining_agents:
            state['next_step'] = remaining_agents[0]
        else:
            state['next_step'] = 'planner'
        
        logger.info(f"Completed {agent_name}, next: {state['next_step']}")
        
    except Exception as e:
        logger.error(f"Error executing {agent_name}: {e}")
        # 即使出错也标记为完成，继续执行其他 Agent
        if agent_name not in state['completed_agents']:
            state['completed_agents'].append(agent_name)
        
        remaining_agents = [a for a in state['agents_to_run'] if a not in state['completed_agents']]
        state['next_step'] = remaining_agents[0] if remaining_agents else 'planner'
    
    return state


# 包装函数，用于 LangGraph
def create_attraction_node():
    async def node(state: AgentState) -> AgentState:
        return await dynamic_agent_node(state, 'attraction')
    return node

def create_weather_node():
    async def node(state: AgentState) -> AgentState:
        return await dynamic_agent_node(state, 'weather')
    return node

def create_hotel_node():
    async def node(state: AgentState) -> AgentState:
        return await dynamic_agent_node(state, 'hotel')
    return node


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


# 路由函数
def route_after_router(state: AgentState) -> str:
    """路由决策后的下一步"""
    return state['next_step']

def route_after_agent(state: AgentState) -> str:
    """Agent 执行后的路由"""
    return state['next_step']


# 构建工作流
def create_workflow():
    """创建 LangGraph 工作流 - 支持动态路由"""
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("router", router_node)
    workflow.add_node("attraction", create_attraction_node())
    workflow.add_node("weather", create_weather_node())
    workflow.add_node("hotel", create_hotel_node())
    workflow.add_node("planner", planner_node)
    
    # 设置入口点：先进行路由决策
    workflow.set_entry_point("router")
    
    # 从 router 到第一个 Agent
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "attraction": "attraction",
            "weather": "weather",
            "hotel": "hotel",
            "planner": "planner"  # 如果不需要任何 Agent，直接规划
        }
    )
    
    # Agent 之间的动态路由
    workflow.add_conditional_edges(
        "attraction",
        route_after_agent,
        {
            "weather": "weather",
            "hotel": "hotel",
            "planner": "planner"
        }
    )
    
    workflow.add_conditional_edges(
        "weather",
        route_after_agent,
        {
            "attraction": "attraction",
            "hotel": "hotel",
            "planner": "planner"
        }
    )
    
    workflow.add_conditional_edges(
        "hotel",
        route_after_agent,
        {
            "attraction": "attraction",
            "weather": "weather",
            "planner": "planner"
        }
    )
    
    # Planner 结束后结束工作流
    workflow.add_edge("planner", END)
    
    # 编译
    app = workflow.compile()
    
    logger.info("Dynamic LangGraph workflow created successfully")
    
    return app


# 全局工作流实例
workflow_app = create_workflow()
