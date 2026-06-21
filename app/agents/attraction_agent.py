"""
景点推荐 Agent
"""
from app.agents.base_agent import BaseAgent
from app.mcp.amap_service import amap_service
from app.mcp.tools import amap_tools
from app.models.model_router import ModelTier
from app.rag.retriever import hybrid_retriever
from app.rag.reranker import reranker
from typing import Dict, Any, List
from app.utils.prompt_templates import ATTRACTION_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


class AttractionAgent(BaseAgent):
    """景点推荐 Agent"""
    
    def __init__(self):
        # 只传入搜索工具，让LLM可以动态调用,绑定STANDARD模型(设计时确定)
        tools = [amap_tools[0]]  # search_poi tool
        super().__init__(name="attraction", cache_enabled=True, tools=tools, model_tier=ModelTier.STANDARD)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行景点推荐
        input_data: {
            'query': 用户查询,
            'location': 位置/城市,
            'preferences': 偏好（可选）,
            'budget': 预算（可选）
        }
        """
        query = input_data.get('query', '')
        location = input_data.get('location', '北京')
        preferences = input_data.get('preferences', '')
        budget = input_data.get('budget', '中等')
        
        logger.info(f"AttractionAgent processing: query={query}, location={location}")
        
        # 生成缓存键
        cache_key = self._get_cache_key(query=query, location=location)
        
        # 步骤 1: RAG 检索相关知识
        rag_results = await self._retrieve_knowledge(query, location)
        
        # 步骤 2: 使用工具调用搜索景点（LLM动态决定）
        attractions = await self._search_attractions_with_tools(query, location)
        
        # 步骤 3: 结合 RAG 和 API 结果生成推荐
        recommendation = await self._generate_recommendation(
            query, location, preferences, budget, 
            rag_results, attractions
        )
        
        return {
            'agent': self.name,
            'recommendation': recommendation,
            'attractions': attractions[:10],
            'knowledge': rag_results,
            'status': 'success'
        }
    
    async def _search_attractions_with_tools(self, query: str, location: str) -> List[Dict]:
        """使用工具调用搜索景点"""
        try:
            # 直接调用高德 API（更可靠，避免 LLM 解析问题）
            keywords = query if query else f"{location} 旅游景点"
            logger.info(f"Directly calling amap_service for attractions: {keywords}")
            return await amap_service.search_poi(
                keywords=keywords,
                city=location,
                types="旅游景点"
            )
        except Exception as e:
            logger.error(f"Attraction search failed: {e}")
            return []
    
    async def _retrieve_knowledge(self, query: str, location: str) -> List[Dict]:
        """检索旅游知识库"""
        # 混合检索
        search_query = f"{location} {query} 旅游攻略"
        results = hybrid_retriever.hybrid_search(search_query, top_k=10)
        
        # Rerank 重排序
        if results:
            ranked_results = reranker.rerank(search_query, results, top_k=5)
            return ranked_results
        
        return results
    
    async def _generate_recommendation(self, query: str, location: str,
                                      preferences: str, budget: str,
                                      rag_results: List[Dict], 
                                      attractions: List[Dict]) -> str:
        """生成推荐理由和建议"""
        # 构建上下文
        knowledge_context = "\n".join([
            r['document'] for r in rag_results[:3]
        ]) if rag_results else "暂无相关知识"
        
        attraction_names = "\n".join([
            f"- {a['name']} (评分: {a.get('rating', 'N/A')})"
            for a in attractions[:5]
        ]) if attractions else "暂无搜索结果"
        
        # 创建 Prompt
        prompt = self._create_prompt(
            ATTRACTION_PROMPT,
            query=query,
            location=location,
            preferences=preferences,
            budget=budget,
            knowledge=knowledge_context,
            attractions=attraction_names
        )
        
        # 调用 LLM（使用设计时绑定的STANDARD模型）
        cache_key = self._get_cache_key(
            action="recommend",
            query=query,
            location=location
        )
        
        recommendation = await self._call_llm(prompt, cache_key=cache_key)
        
        return recommendation


# 全局景点 Agent 实例
attraction_agent = AttractionAgent()
