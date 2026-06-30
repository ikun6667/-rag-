"""
多 Agent 旅游规划系统 - 主入口
"""
# 加载环境变量（必须在最前面）
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.core.config import settings
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info("Starting Multi-Agent Travel Planning System...")
    
    # 初始化数据库
    try:
        from app.core.database import init_database
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    logger.info("System started successfully")
    yield
    # 关闭事件
    logger.info("Shutting down system...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Multi-Agent Travel Planning System",
    description="基于 LangChain、LangGraph 和多 Agent 的智能旅游规划系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS（从配置读取允许的域名）
_cors_origins = [
    origin.strip() 
    for origin in settings.CORS_ORIGINS.split(",") 
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# API Key 鉴权中间件
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """
    API Key 鉴权中间件
    
    - 健康检查 /health 不需要鉴权
    - 如果配置了 API_KEY，其他接口需在 Header 中携带 X-API-Key
    """
    # 跳过不需要鉴权的路径
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)
    
    # 如果未配置 API_KEY，跳过鉴权（开发模式）
    if not settings.API_KEY:
        return await call_next(request)
    
    # 校验 API Key
    api_key = request.headers.get("X-API-Key", "")
    if api_key != settings.API_KEY:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid or missing API Key"}
        )
    
    return await call_next(request)


# 注册路由
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
