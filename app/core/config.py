"""
系统核心配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """系统配置"""
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "travel_planner"
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # ChromaDB 配置
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    
    # LLM 配置 - 主模型
    LLM_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    LLM_API_BASE: str = "http://localhost:8001/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    
    # 多模型路由配置
    # 快速模型：用于简单任务(天气查询、基础检索)
    FAST_MODEL_NAME: str = "Qwen/Qwen2.5-3B-Instruct"
    FAST_MODEL_API_BASE: str = "http://localhost:8002/v1"
    FAST_MODEL_TEMPERATURE: float = 0.5
    FAST_MODEL_MAX_TOKENS: int = 1024
    
    # 标准模型：用于常规任务(景点推荐、酒店搜索)
    STANDARD_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    STANDARD_MODEL_API_BASE: str = "http://localhost:8001/v1"
    STANDARD_MODEL_TEMPERATURE: float = 0.7
    STANDARD_MODEL_MAX_TOKENS: int = 2048
    
    # 高级模型：用于复杂任务(行程规划、综合分析)
    ADVANCED_MODEL_NAME: str = "Qwen/Qwen2.5-14B-Instruct"
    ADVANCED_MODEL_API_BASE: str = "http://localhost:8003/v1"
    ADVANCED_MODEL_TEMPERATURE: float = 0.8
    ADVANCED_MODEL_MAX_TOKENS: int = 4096
    
    # Embedding 配置
    EMBEDDING_MODEL: str = os.path.expanduser("~/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181")  # 使用本地模型路径
    EMBEDDING_DIMENSION: int = 1024
    
    # HuggingFace 配置
    HF_ENDPOINT: str = "https://hf-mirror.com"  # 国内镜像源
    
    # RAG 配置
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.7
    RRF_K_VALUE: int = 60
    
    # 高德地图 API
    AMAP_API_KEY: str = ""
    
    # 缓存配置
    CACHE_TTL: int = 3600  # 秒
    
    # 上下文配置
    MAX_CONTEXT_LENGTH: int = 4096
    CONTEXT_COMPRESS_RATIO: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
