"""
系统核心配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import glob


def _resolve_hf_model_path(model_name: str) -> str:
    """
    解析 HuggingFace 模型路径。
    
    如果是本地路径（存在）直接返回；
    如果是 HF 模型名（如 BAAI/bge-m3），检查本地缓存是否已下载，
    有则使用缓存路径（避免重复下载），否则返回原名（触发自动下载）。
    """
    # 如果是本地路径且存在，直接返回
    if os.path.isdir(model_name):
        return model_name
    
    # 检查 HuggingFace 本地缓存
    hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
    # 模型名格式: "org/model-name" -> 缓存目录: "models--org--model-name"
    safe_name = "models--" + model_name.replace("/", "--")
    model_cache_dir = os.path.join(hf_cache, safe_name)
    
    if os.path.isdir(model_cache_dir):
        # 查找最新的完整 snapshot（跳过不完整的下载）
        snapshots_dir = os.path.join(model_cache_dir, "snapshots")
        if os.path.isdir(snapshots_dir):
            snapshot_dirs = sorted(glob.glob(os.path.join(snapshots_dir, "*")), reverse=True)
            for snap_dir in snapshot_dirs:
                # 检查 snapshot 是否完整（至少包含 config.json、模型文件和 sentence-transformers 兼容配置）
                has_config = os.path.isfile(os.path.join(snap_dir, "config.json"))
                # 检查是否有模型权重文件（.bin 或 .safetensors）
                has_model = (
                    glob.glob(os.path.join(snap_dir, "*.bin")) or
                    glob.glob(os.path.join(snap_dir, "*.safetensors")) or
                    glob.glob(os.path.join(snap_dir, "model*"))
                )
                # 检查 sentence-transformers 兼容性（1_Pooling 目录）
                has_pooling = os.path.isdir(os.path.join(snap_dir, "1_Pooling"))
                if has_config and has_model and has_pooling:
                    return snap_dir
    
    # 未找到本地缓存，返回原名（将触发联网下载）
    return model_name


class Settings(BaseSettings):
    """系统配置"""
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS 配置（生产环境请限制为具体域名）
    CORS_ORIGINS: str = "*"  # 多个域名用逗号分隔，如 "https://example.com,https://app.example.com"
    
    # API 鉴权（设置后客户端需在 Header 中携带 X-API-Key）
    API_KEY: str = ""  # 为空则不启用鉴权（开发环境），生产环境务必设置
    
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
    EMBEDDING_MODEL: str = "BAAI/bge-m3"  # HuggingFace 模型名称，支持本地路径或远程模型
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

# 解析 Embedding 模型路径（自动检测本地缓存）
settings.EMBEDDING_MODEL = _resolve_hf_model_path(settings.EMBEDDING_MODEL)
