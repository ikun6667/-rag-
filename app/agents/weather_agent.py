"""
天气查询 Agent - 固定使用FAST小模型
"""
from app.agents.base_agent import BaseAgent
from app.mcp.amap_service import amap_service
from app.mcp.tools import amap_tools
from app.models.model_router import ModelTier
from typing import Dict, Any
from app.utils.prompt_templates import WEATHER_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WeatherAgent(BaseAgent):
    """天气查询 Agent"""
    
    def __init__(self):
        # 天气查询是简单任务,固定使用FAST小模型(设计时确定)
        tools = [amap_tools[1]]  # get_weather tool
        super().__init__(name="weather", cache_enabled=True, tools=tools)
        
        # 绑定专属FAST模型(零运行时开销)
        from app.models.llm_client import llm_client
        self.dedicated_model = llm_client.get_model_by_tier(ModelTier.FAST)
        logger.info(f"WeatherAgent initialized with fixed FAST model")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行天气查询
        input_data: {
            'location': 城市名称,
            'date': 日期（可选，默认今天）
        }
        """
        location = input_data.get('location', '北京')
        date = input_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        logger.info(f"WeatherAgent processing: location={location}, date={date}")
        
        # 生成缓存键
        cache_key = self._get_cache_key(location=location, date=date)
        
        # 使用工具调用获取天气（LLM动态决定）
        weather_data = await self._get_weather_with_tools(location)
        
        if not weather_data:
            return {
                'agent': self.name,
                'weather': {},
                'suggestion': '无法获取天气信息',
                'status': 'error'
            }
        
        # 生成出行建议（传入 date 用于缓存）
        suggestion = await self._generate_suggestion(weather_data, location, date)
        
        return {
            'agent': self.name,
            'weather': weather_data,
            'suggestion': suggestion,
            'status': 'success'
        }
    
    async def _get_weather_with_tools(self, location: str) -> Dict:
        """使用工具调用获取天气"""
        try:
            # 直接调用高德 API（更可靠）
            logger.info(f"Directly calling amap_service for weather")
            return await amap_service.get_weather(city=location)
        except Exception as e:
            logger.error(f"Weather query failed: {e}")
            return {}
    
    async def _generate_suggestion(self, weather_data: Dict, location: str, date: str = None) -> str:
        """根据天气生成出行建议"""
        prompt = self._create_prompt(
            WEATHER_PROMPT,
            location=location,
            weather=str(weather_data)
        )
        
        # 缓存键包含 date，避免不同日期的天气建议混淆
        cache_params = {"action": "suggestion", "location": location}
        if date:
            cache_params["date"] = date
        cache_key = self._get_cache_key(**cache_params)
        
        # 直接使用专属FAST模型(无需路由,零开销)
        result = await self.dedicated_model.ainvoke(prompt)
        suggestion = result.content if hasattr(result, 'content') else str(result)
        
        # 保存到缓存
        if self.cache_enabled and cache_key:
            self._set_to_cache(cache_key, suggestion)
        
        return suggestion


# 全局天气 Agent 实例
weather_agent = WeatherAgent()
