"""
大语言模型客户端 - 支持多模型路由和熔断器
"""
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.models.model_router import model_router, ModelTier, ModelConfig
from app.models.circuit_breaker import circuit_breakers, retry_with_fallback, LLMCallFailedError
from app.utils.token_manager import token_manager

from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端封装 - 支持多模型路由"""
    
    def __init__(self):
        # 缓存已创建的模型实例
        self._model_cache: Dict[ModelTier, ChatOpenAI] = {}
        
        logger.info("LLM Client initialized with multi-model routing support")
    
    def _get_or_create_model(self, tier: ModelTier) -> ChatOpenAI:
        """
        获取或创建指定等级的模型实例（带缓存）
        
        Args:
            tier: 模型等级
            
        Returns:
            ChatOpenAI 实例
        """
        if tier in self._model_cache:
            return self._model_cache[tier]
        
        # 获取模型配置
        config = model_router.get_model_config(tier)
        
        # 创建新模型实例
        model = ChatOpenAI(
            model=config.name,
            openai_api_base=config.api_base,
            openai_api_key=settings.LLM_API_KEY,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        
        # 缓存模型实例
        self._model_cache[tier] = model
        logger.info(f"Created {tier.value} model: {config.name}")
        
        return model
    
    @property
    def chat_model(self) -> ChatOpenAI:
        """默认使用标准模型（保持向后兼容）"""
        return self._get_or_create_model(ModelTier.STANDARD)
    
    def get_model_by_tier(self, tier: ModelTier) -> ChatOpenAI:
        """根据模型等级获取模型"""
        return self._get_or_create_model(tier)
    
    def get_model_by_task(self, task_type: str) -> ChatOpenAI:
        """
        根据任务类型自动选择合适的模型
        
        Args:
            task_type: 任务类型标识
            
        Returns:
            合适的 ChatOpenAI 实例
        """
        tier = model_router.route_by_task(task_type)
        return self._get_or_create_model(tier)
    
    def generate(self, prompt: str, task_type: Optional[str] = None, 
                check_token_limit: bool = True, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            task_type: 任务类型，用于自动选择模型
            check_token_limit: 是否检查 token 限制
        """
        try:
            # Token 检查和截断
            if check_token_limit:
                # 获取当前模型的 max_tokens 配置
                if task_type:
                    tier = model_router.route_by_task(task_type)
                else:
                    tier = ModelTier.STANDARD
                
                config = model_router.get_model_config(tier)
                max_tokens = config.max_tokens
                
                # 检查并优化 prompt
                token_manager.check_and_warn(prompt, threshold=max_tokens * 0.8)
                
                # 如果超过阈值,自动截断
                estimated_tokens = token_manager.estimate_tokens(prompt)
                if estimated_tokens > max_tokens * 0.9:
                    logger.warning(f"Prompt approaching limit ({estimated_tokens}/{max_tokens}), truncating...")
                    prompt = token_manager.truncate_text(prompt, int(max_tokens * 0.85))
            
            # 根据任务类型选择模型
            if task_type:
                model = self.get_model_by_task(task_type)
            else:
                model = self.chat_model
            
            response = model.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    async def generate_async(self, prompt: str, task_type: Optional[str] = None, 
                            use_circuit_breaker: bool = True,
                            check_token_limit: bool = True, **kwargs) -> str:
        """
        异步生成文本(带熔断器和重试降级)
        
        Args:
            prompt: 提示词
            task_type: 任务类型，用于自动选择模型
            use_circuit_breaker: 是否使用熔断器保护
            check_token_limit: 是否检查 token 限制
        """
        # Token 检查和截断
        if check_token_limit:
            # 获取当前模型的 max_tokens 配置
            if task_type:
                tier = model_router.route_by_task(task_type)
            else:
                tier = ModelTier.STANDARD
            
            config = model_router.get_model_config(tier)
            max_tokens = config.max_tokens
            
            # 检查并优化 prompt
            token_manager.check_and_warn(prompt, threshold=max_tokens * 0.8)
            
            # 如果超过阈值,自动截断
            estimated_tokens = token_manager.estimate_tokens(prompt)
            if estimated_tokens > max_tokens * 0.9:
                logger.warning(f"Prompt approaching limit ({estimated_tokens}/{max_tokens}), truncating...")
                prompt = token_manager.truncate_text(prompt, int(max_tokens * 0.85))
        
        # 选择模型
        if task_type:
            tier = model_router.route_by_task(task_type)
        else:
            tier = ModelTier.STANDARD
        
        model = self._get_or_create_model(tier)
        
        # 定义主调用函数
        async def primary_call():
            return await model.ainvoke(prompt)
        
        # 定义降级函数(使用更小一级的模型)
        fallback_tier = self._get_fallback_tier(tier)
        fallback_model = self._get_or_create_model(fallback_tier)
        
        async def fallback_call():
            logger.warning(f"Using fallback model: {fallback_tier.value}")
            return await fallback_model.ainvoke(prompt)
        
        try:
            if use_circuit_breaker:
                # 使用熔断器+重试降级
                breaker = circuit_breakers.get(tier.value)
                if breaker:
                    result = await breaker.call(primary_call)
                else:
                    result = await primary_call()
            else:
                # 不使用熔断器,直接调用
                result = await primary_call()
            
            return result.content
            
        except Exception as e:
            logger.error(f"Primary model failed, attempting fallback: {e}")
            
            # 尝试降级
            try:
                result = await retry_with_fallback.execute(
                    primary_call,
                    fallback_func=fallback_call
                )
                return result.content
            except LLMCallFailedError as final_error:
                logger.error(f"All models failed: {final_error}")
                raise
    
    def generate_with_params(self, prompt: str, 
                            temperature: Optional[float] = None,
                            top_k: Optional[int] = None,
                            max_tokens: Optional[int] = None) -> str:
        """使用自定义参数生成"""
        original_temp = self.temperature
        original_max_tokens = self.max_tokens
        
        try:
            if temperature is not None:
                self.temperature = temperature
            if max_tokens is not None:
                self.max_tokens = max_tokens
            
            return self.generate(prompt)
        finally:
            self.temperature = original_temp
            self.max_tokens = original_max_tokens
    
    def _get_fallback_tier(self, current_tier: ModelTier) -> ModelTier:
        """
        获取降级模型等级
        
        Args:
            current_tier: 当前模型等级
            
        Returns:
            降级后的模型等级
        """
        fallback_map = {
            ModelTier.ADVANCED: ModelTier.STANDARD,  # 14B → 7B
            ModelTier.STANDARD: ModelTier.FAST,      # 7B → 3B
            ModelTier.FAST: ModelTier.FAST,          # 3B → 3B (最低了)
        }
        return fallback_map.get(current_tier, ModelTier.FAST)


# 全局 LLM 实例
llm_client = LLMClient()
