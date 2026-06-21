"""
模型路由器 - 根据任务类型智能选择合适的 LLM 模型
"""
from enum import Enum
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """模型等级"""
    FAST = "fast"           # 快速模型：简单任务
    STANDARD = "standard"   # 标准模型：常规任务
    ADVANCED = "advanced"   # 高级模型：复杂任务


class ModelConfig:
    """模型配置"""
    def __init__(self, name: str, api_base: str, temperature: float, max_tokens: int):
        self.name = name
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens


class ModelRouter:
    """
    模型路由器
    
    根据任务复杂度、响应时间要求、成本考虑等因素，
    智能选择最合适的 LLM 模型。
    
    路由策略：
    - FAST: 天气查询、简单问答、基础检索 (< 1s)
    - STANDARD: 景点推荐、酒店搜索、内容生成 (1-3s)
    - ADVANCED: 行程规划、综合分析、创意写作 (3-5s)
    """
    
    def __init__(self):
        # 初始化各等级模型配置
        self.models: Dict[ModelTier, ModelConfig] = {
            ModelTier.FAST: ModelConfig(
                name=settings.FAST_MODEL_NAME,
                api_base=settings.FAST_MODEL_API_BASE,
                temperature=settings.FAST_MODEL_TEMPERATURE,
                max_tokens=settings.FAST_MODEL_MAX_TOKENS
            ),
            ModelTier.STANDARD: ModelConfig(
                name=settings.STANDARD_MODEL_NAME,
                api_base=settings.STANDARD_MODEL_API_BASE,
                temperature=settings.STANDARD_MODEL_TEMPERATURE,
                max_tokens=settings.STANDARD_MODEL_MAX_TOKENS
            ),
            ModelTier.ADVANCED: ModelConfig(
                name=settings.ADVANCED_MODEL_NAME,
                api_base=settings.ADVANCED_MODEL_API_BASE,
                temperature=settings.ADVANCED_MODEL_TEMPERATURE,
                max_tokens=settings.ADVANCED_MODEL_MAX_TOKENS
            )
        }
        
        logger.info(f"Model Router initialized with {len(self.models)} model tiers")
    
    def route_by_task(self, task_type: str, **kwargs) -> ModelTier:
        """
        根据任务类型路由到合适的模型
        
        Args:
            task_type: 任务类型标识
            kwargs: 额外参数
            
        Returns:
            推荐的模型等级
        """
        # 任务类型映射规则
        routing_rules = {
            # 快速模型任务
            "weather_query": ModelTier.FAST,
            "simple_qa": ModelTier.FAST,
            "basic_retrieval": ModelTier.FAST,
            
            # 标准模型任务
            "attraction_search": ModelTier.STANDARD,
            "hotel_search": ModelTier.STANDARD,
            "content_generation": ModelTier.STANDARD,
            "recommendation": ModelTier.STANDARD,
            
            # 高级模型任务
            "itinerary_planning": ModelTier.ADVANCED,
            "complex_analysis": ModelTier.ADVANCED,
            "creative_writing": ModelTier.ADVANCED,
            "multi_agent_synthesis": ModelTier.ADVANCED,
        }
        
        # 查找匹配的规则
        if task_type in routing_rules:
            tier = routing_rules[task_type]
            logger.debug(f"Task '{task_type}' routed to {tier.value} model")
            return tier
        
        # 默认使用标准模型
        logger.warning(f"Unknown task type '{task_type}', using standard model")
        return ModelTier.STANDARD
    
    def route_by_complexity(self, complexity_score: float) -> ModelTier:
        """
        根据复杂度评分路由模型
        
        Args:
            complexity_score: 复杂度评分 (0-1)
            
        Returns:
            推荐的模型等级
        """
        if complexity_score < 0.3:
            return ModelTier.FAST
        elif complexity_score < 0.7:
            return ModelTier.STANDARD
        else:
            return ModelTier.ADVANCED
    
    def get_model_config(self, tier: ModelTier) -> ModelConfig:
        """获取指定等级的模型配置"""
        if tier not in self.models:
            raise ValueError(f"Unknown model tier: {tier}")
        return self.models[tier]
    
    def get_default_tier(self) -> ModelTier:
        """获取默认模型等级"""
        return ModelTier.STANDARD


# 全局模型路由器实例
model_router = ModelRouter()
