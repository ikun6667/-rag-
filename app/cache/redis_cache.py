"""
Redis 缓存层
"""
from app.core.database import redis_client
from app.core.config import settings
import json
import hashlib
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = None):
        self.default_ttl = default_ttl or settings.CACHE_TTL
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_data = "|".join(str(arg) for arg in args)
        hash_value = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False)
            redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def get_or_compute(self, key: str, compute_func, ttl: int = None) -> Any:
        """获取或计算（缓存穿透保护）"""
        value = self.get(key)
        if value is not None:
            return value
        
        # 计算新值
        value = compute_func()
        if value is not None:
            self.set(key, value, ttl)
        
        return value


# 缓存键前缀常量
class CacheKeys:
    ATTRACTION = "attraction"
    WEATHER = "weather"
    HOTEL = "hotel"
    RAG_RESULT = "rag"
    LLM_RESPONSE = "llm"
    TRIP_PLAN = "trip_plan"


# 全局缓存管理器
cache_manager = CacheManager()
