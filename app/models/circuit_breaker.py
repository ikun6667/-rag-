"""
LLM调用熔断器和容错机制
"""
import time
import asyncio
from typing import Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 正常状态,允许请求
    OPEN = "open"           # 熔断状态,拒绝请求
    HALF_OPEN = "half_open" # 半开状态,尝试恢复


class CircuitBreaker:
    """
    熔断器实现
    
    保护LLM调用,防止连续失败导致系统雪崩:
    - 连续失败N次 → 进入OPEN状态(拒绝请求)
    - 等待T秒后 → 进入HALF_OPEN状态(允许一次试探)
    - 试探成功 → 回到CLOSED状态
    - 试探失败 → 回到OPEN状态
    """
    
    def __init__(self, 
                 failure_threshold: int = 3,    # 失败阈值
                 recovery_timeout: int = 30,     # 恢复超时(秒)
                 expected_exception: type = Exception):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 连续失败多少次后熔断
            recovery_timeout: 熔断后多少秒尝试恢复
            expected_exception: 需要捕获的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"CircuitBreaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def _should_allow_request(self) -> bool:
        """判断是否允许请求"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # 检查是否超过恢复超时
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker state changed: OPEN → HALF_OPEN")
                return True
            return False
        
        # HALF_OPEN状态允许一次试探
        return True
    
    def _record_success(self):
        """记录成功"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker state changed: HALF_OPEN → CLOSED (recovered)")
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def _record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            old_state = self.state
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker state changed: {old_state.value} → OPEN "
                f"(failures={self.failure_count})"
            )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            Exception: 如果熔断器处于OPEN状态或函数执行失败
        """
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN. Failures: {self.failure_count}, "
                f"Last failure: {self.last_failure_time}"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            logger.error(f"Circuit breaker recorded failure: {e}")
            raise


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class RetryWithFallback:
    """
    重试+降级机制
    
    策略:
    1. 主模型失败 → 重试N次
    2. 仍然失败 → 降级到备用模型
    3. 备用也失败 → 返回错误信息
    """
    
    def __init__(self, 
                 max_retries: int = 2,          # 最大重试次数
                 fallback_model_getter: Callable = None):  # 备用模型获取函数
        """
        初始化重试降级器
        
        Args:
            max_retries: 最大重试次数
            fallback_model_getter: 获取备用模型的函数
        """
        self.max_retries = max_retries
        self.fallback_model_getter = fallback_model_getter
    
    async def execute(self, 
                     primary_func: Callable,
                     *args,
                     fallback_func: Callable = None,
                     **kwargs) -> Any:
        """
        执行带重试和降级的调用
        
        Args:
            primary_func: 主函数(使用主模型)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        last_error = None
        
        # 第1步: 重试主模型
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries}")
                    # 指数退避
                    await asyncio.sleep(2 ** attempt)
                
                result = await primary_func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Primary model failed (attempt {attempt + 1}): {e}")
        
        # 第2步: 降级到备用模型
        if fallback_func:
            logger.warning("Primary model exhausted retries, falling back to secondary model")
            try:
                result = await fallback_func(*args, **kwargs)
                logger.info("Fallback model succeeded")
                return result
            except Exception as e:
                logger.error(f"Fallback model also failed: {e}")
                last_error = e
        
        # 第3步: 所有尝试都失败
        raise LLMCallFailedError(
            f"All attempts failed. Last error: {last_error}"
        ) from last_error


class LLMCallFailedError(Exception):
    """LLM调用失败异常"""
    pass


# 全局熔断器实例(按模型等级隔离)
circuit_breakers = {
    "fast": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "standard": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "advanced": CircuitBreaker(failure_threshold=2, recovery_timeout=60),  # 高级模型更严格
}

# 全局重试降级器
retry_with_fallback = RetryWithFallback(max_retries=2)
