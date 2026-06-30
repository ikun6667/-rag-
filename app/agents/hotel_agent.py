"""
酒店预订 Agent
"""
from app.agents.base_agent import BaseAgent
from app.mcp.amap_service import amap_service
from app.mcp.tools import amap_tools
from app.rag.retriever import hybrid_retriever
from typing import Dict, Any, List
from app.utils.prompt_templates import HOTEL_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import json

logger = logging.getLogger(__name__)


class HotelAgent(BaseAgent):
    """酒店预订 Agent"""
    
    def __init__(self):
        # 传入酒店搜索工具
        tools = [amap_tools[0]]  # search_poi tool (用于搜索酒店)
        super().__init__(name="hotel", cache_enabled=True, tools=tools)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行酒店搜索
        input_data: {
            'location': 城市/区域,
            'check_in': 入住日期,
            'check_out': 退房日期,
            'budget': 预算范围,
            'preferences': 偏好（可选）
        }
        """
        location = input_data.get('location', '北京')
        check_in = input_data.get('check_in', '')
        check_out = input_data.get('check_out', '')
        budget = input_data.get('budget', '中等')
        preferences = input_data.get('preferences', '')
        
        logger.info(f"HotelAgent processing: location={location}")
        
        # 生成缓存键
        cache_key = self._get_cache_key(
            location=location,
            budget=budget
        )
        
        # 步骤 1: RAG 检索酒店建议
        rag_results = await self._retrieve_hotel_knowledge(location, budget)
        
        # 步骤 2: 使用工具调用搜索酒店（LLM动态决定）
        hotels = await self._search_hotels_with_tools(location, budget)
        
        # 步骤 3: 生成推荐
        recommendation = await self._generate_recommendation(
            location, budget, preferences, rag_results, hotels
        )
        
        return {
            'agent': self.name,
            'recommendation': recommendation,
            'hotels': hotels[:10],
            'knowledge': rag_results,
            'status': 'success'
        }
    
    async def _search_hotels_with_tools(self, location: str, budget: str) -> List[Dict]:
        """使用工具调用搜索酒店"""
        try:
            # 构建消息
            system_message = SystemMessage(
                content="你是一个酒店推荐助手。使用 search_poi 工具搜索用户指定城市的酒店信息，types参数应设置为'住宿服务'。"
            )
            human_message = HumanMessage(
                content=f"请在{location}搜索{budget}价位的酒店，类型为住宿服务"
            )
            
            messages = [system_message, human_message]
            
            # 调用带工具的LLM
            result = await self._call_llm_with_tools(messages, max_iterations=2)
            
            # 解析JSON结果
            try:
                if '[' in result and '{' in result:
                    start_idx = result.find('[')
                    end_idx = result.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        return json.loads(json_str)
            except (json.JSONDecodeError, ValueError, IndexError):
                pass
            
            # 如果解析失败，回退到直接调用
            logger.warning("Tool calling failed, falling back to direct call")
            return await amap_service.search_poi(
                keywords=f"{location} 酒店",
                city=location,
                types="住宿服务"
            )
        except Exception as e:
            logger.error(f"Tool-based hotel search failed: {e}")
            # 出错时回退到直接调用
            return await amap_service.search_poi(
                keywords=f"{location} 酒店",
                city=location,
                types="住宿服务"
            )
    
    async def _retrieve_hotel_knowledge(self, location: str, 
                                       budget: str) -> List[Dict]:
        """检索酒店相关知识"""
        search_query = f"{location} {budget} 酒店住宿推荐"
        results = hybrid_retriever.hybrid_search(search_query, top_k=5)
        return results
    
    async def _generate_recommendation(self, location: str, budget: str,
                                      preferences: str, rag_results: List[Dict],
                                      hotels: List[Dict]) -> str:
        """生成酒店推荐"""
        knowledge_context = "\n".join([
            r['document'] for r in rag_results[:2]
        ]) if rag_results else "暂无相关知识"
        
        hotel_list = "\n".join([
            f"- {h['name']} (价格: {h.get('price', '未知')})"
            for h in hotels[:5]
        ]) if hotels else "暂无搜索结果"
        
        prompt = self._create_prompt(
            HOTEL_PROMPT,
            location=location,
            budget=budget,
            preferences=preferences,
            knowledge=knowledge_context,
            hotels=hotel_list
        )
        
        cache_key = self._get_cache_key(
            action="recommend",
            location=location,
            budget=budget
        )
        
        recommendation = await self._call_llm(
            prompt, 
            cache_key=cache_key,
            task_type="hotel_search"
        )
        
        return recommendation


# 全局酒店 Agent 实例
hotel_agent = HotelAgent()
