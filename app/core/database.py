"""
数据库连接管理
"""
import os
# 禁用 ChromaDB 遥测以避免 posthog 兼容性报错
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import redis
import chromadb


# MySQL 引擎
engine = create_engine(
    f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis 连接
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)


# ChromaDB 客户端（遥测已在文件顶部禁用）
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
