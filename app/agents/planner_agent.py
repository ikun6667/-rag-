"""
行程规划 Agent - 协调整合各子 Agent,支持动态模型切换
"""
from app.agents.base_agent import BaseAgent
from app.agents.attraction_agent import attraction_agent
from app.agents.weather_agent import weather_agent
from app.agents.hotel_agent import hotel_agent
from app.models.model_router import ModelTier
from typing import Dict, Any, List
from app.utils.prompt_templates import PLANNER_PROMPT
import logging

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """行程规划 Agent"""
    
    def __init__(self):
        super().__init__(name="planner", cache_enabled=True)
        self.sub_agents = {
            'attraction': attraction_agent,
            'weather': weather_agent,
            'hotel': hotel_agent
        }
        
        # Planner是复杂Agent,支持动态切换模型(默认ADVANCED)
        from app.models.llm_client import llm_client
        self.primary_model = llm_client.get_model_by_tier(ModelTier.ADVANCED)  # 14B
        self.fallback_model = llm_client.get_model_by_tier(ModelTier.STANDARD)  # 7B降级
        logger.info(f"PlannerAgent initialized with dynamic model switching (ADVANCED/STANDARD)")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行行程规划
        input_data: {
            'query': 用户需求,
            'location': 目的地,
            'days': 天数,
            'budget': 预算,
            'preferences': 偏好
        }
        """
        query = input_data.get('query', '')
        location = input_data.get('location', '北京')
        days = input_data.get('days', 3)
        budget = input_data.get('budget', '中等')
        preferences = input_data.get('preferences', '')
        
        logger.info(f"PlannerAgent processing: location={location}, days={days}")
        
        # 生成缓存键
        cache_key = self._get_cache_key(
            query=query,
            location=location,
            days=days
        )
        
        # 步骤 1: 并行调用子 Agent
        sub_results = await self._invoke_sub_agents(
            query, location, budget, preferences
        )
        
        # 步骤 2: 整合结果生成完整行程
        itinerary = await self._generate_itinerary(
            query, location, days, budget, preferences, sub_results
        )
        
        return {
            'agent': self.name,
            'itinerary': itinerary,
            'sub_agent_results': sub_results,
            'status': 'success'
        }
    
    async def _invoke_sub_agents(self, query: str, location: str,
                                budget: str, preferences: str) -> Dict[str, Any]:
        """并行调用子 Agent"""
        results = {}
        
        try:
            # 景点推荐
            attraction_result = await attraction_agent.execute({
                'query': query,
                'location': location,
                'preferences': preferences,
                'budget': budget
            })
            results['attraction'] = attraction_result
            
            # 天气查询
            weather_result = await weather_agent.execute({
                'location': location
            })
            results['weather'] = weather_result
            
            # 酒店推荐
            hotel_result = await hotel_agent.execute({
                'location': location,
                'budget': budget,
                'preferences': preferences
            })
            results['hotel'] = hotel_result
            
        except Exception as e:
            logger.error(f"Sub-agent invocation error: {e}")
        
        return results
    
    async def _generate_itinerary(self, query: str, location: str,
                                 days: int, budget: str, preferences: str,
                                 sub_results: Dict) -> str:
        """生成完整行程"""
        # 提取各 Agent 的结果
        attraction_info = sub_results.get('attraction', {}).get('recommendation', '')
        weather_info = sub_results.get('weather', {}).get('suggestion', '')
        hotel_info = sub_results.get('hotel', {}).get('recommendation', '')
        
        prompt = self._create_prompt(
            PLANNER_PROMPT,
            query=query,
            location=location,
            days=days,
            budget=budget,
            preferences=preferences,
            attractions=attraction_info,
            weather=weather_info,
            hotels=hotel_info
        )
        
        cache_key = self._get_cache_key(
            action="itinerary",
            location=location,
            days=days
        )
        
        # 使用动态模型切换: 先尝试ADVANCED,失败后降级到STANDARD
        try:
            # 主模型调用(带熔断器保护)
            result = await self.primary_model.ainvoke(prompt)
            itinerary = result.content if hasattr(result, 'content') else str(result)
            logger.info("Planner used ADVANCED model successfully")
        except Exception as e:
            logger.warning(f"ADVANCED model failed, falling back to STANDARD: {e}")
            try:
                # 降级到STANDARD模型
                result = await self.fallback_model.ainvoke(prompt)
                itinerary = result.content if hasattr(result, 'content') else str(result)
                logger.info("Planner fallback to STANDARD model succeeded")
            except Exception as fallback_error:
                logger.error(f"Both models failed: {fallback_error}")
                raise
        
        # 保存到缓存
        if self.cache_enabled and cache_key:
            self._set_to_cache(cache_key, itinerary)
        
        return itinerary


# 全局规划 Agent 实例
planner_agent = PlannerAgent()
