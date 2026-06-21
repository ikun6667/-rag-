"""
多 Agent 旅游规划系统 - 主入口
"""
# 加载环境变量（必须在最前面）
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.core.database import init_database
import logging
import uvicorn

# 配置日志
import os
from datetime import datetime

# 创建日志目录
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 生成日志文件名(按日期)
log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
log_filepath = os.path.join(log_dir, log_filename)

# 配置日志：同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler(log_filepath, encoding='utf-8')  # 文件输出
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"日志文件路径: {log_filepath}")

# 创建 FastAPI 应用
app = FastAPI(
    title="Multi-Agent Travel Planning System",
    description="基于 LangChain、LangGraph 和多 Agent 的智能旅游规划系统",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Starting Multi-Agent Travel Planning System...")
    
    # 初始化数据库
    try:
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    logger.info("System started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down system...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
