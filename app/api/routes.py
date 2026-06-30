"""
FastAPI API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.graph.workflow import workflow_app
from app.rag.data_processor import data_processor
from app.core.database import get_db, init_database
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求模型
class TravelQueryRequest(BaseModel):
    """旅游查询请求"""
    query: str
    location: str = "北京"
    days: int = 3
    budget: str = "中等"
    preferences: str = ""


class DataProcessRequest(BaseModel):
    """数据处理请求"""
    data_dir: str = "./data/knowledge_base"
    rebuild_index: bool = True


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: float


# API 端点
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        timestamp=time.time()
    )


@router.post("/api/travel/plan")
async def plan_travel(request: TravelQueryRequest):
    """
    制定旅行行程
    
    Args:
        request: 旅游查询请求
    
    Returns:
        行程规划结果
    """
    try:
        logger.info(f"Received travel plan request: {request}")
        
        # 构建初始状态
        initial_state = {
            "query": request.query,
            "location": request.location,
            "days": request.days,
            "budget": request.budget,
            "preferences": request.preferences,
            "attraction_result": {},
            "weather_result": {},
            "hotel_result": {},
            "plan_result": {},
            "next_step": "",
            "needs_clarification": False,
            "clarification_questions": [],
            "final_response": ""
        }
        
        # 执行工作流
        result = await workflow_app.ainvoke(initial_state)
        
        return {
            "success": True,
            "data": {
                "itinerary": result.get("final_response", ""),
                "details": {
                    "attractions": result.get("attraction_result", {}),
                    "weather": result.get("weather_result", {}),
                    "hotels": result.get("hotel_result", {})
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Travel planning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务内部错误，请稍后重试")


@router.post("/api/data/process")
async def process_data(request: DataProcessRequest):
    """
    处理旅游知识库数据
    
    Args:
        request: 数据处理请求
    
    Returns:
        处理结果统计
    """
    try:
        logger.info(f"Processing data from: {request.data_dir}")
        
        stats = data_processor.process_pipeline(
            data_dir=request.data_dir,
            rebuild_index=request.rebuild_index
        )
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"Data processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="数据处理失败，请检查输入参数")


@router.get("/api/rag/search")
async def search_knowledge(query: str, top_k: int = 5):
    """
    搜索旅游知识
    
    Args:
        query: 搜索查询
        top_k: 返回结果数量
    
    Returns:
        搜索结果
    """
    try:
        from app.rag.retriever import hybrid_retriever
        from app.rag.reranker import reranker
        
        # 混合检索
        results = hybrid_retriever.hybrid_search(query, top_k=top_k * 2)
        
        # Rerank
        if results:
            results = reranker.rerank(query, results, top_k=top_k)
        
        return {
            "success": True,
            "data": results
        }
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="搜索服务暂时不可用")


@router.post("/api/cache/clear")
async def clear_cache(prefix: Optional[str] = None):
    """
    清除缓存
    
    Args:
        prefix: 缓存前缀（可选）
    
    Returns:
        清除结果
    """
    try:
        from app.cache.redis_cache import redis_client
        
        if prefix:
            # 删除指定前缀的缓存
            keys = redis_client.keys(f"{prefix}:*")
            if keys:
                redis_client.delete(*keys)
                count = len(keys)
            else:
                count = 0
        else:
            # 清除所有缓存（谨慎使用）
            redis_client.flushdb()
            count = -1
        
        return {
            "success": True,
            "message": f"Cleared {count} cache entries"
        }
    
    except Exception as e:
        logger.error(f"Cache clear error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="缓存清除失败")


@router.get("/api/stats")
async def get_stats():
    """
    获取系统统计信息
    
    Returns:
        系统统计
    """
    try:
        from app.rag.vector_store import vector_store
        from app.cache.redis_cache import redis_client
        
        # 向量库统计
        vector_count = vector_store.count()
        
        # Redis 统计
        redis_info = redis_client.info('memory')
        cache_memory = redis_info.get('used_memory_human', 'N/A')
        
        return {
            "success": True,
            "data": {
                "vector_store": {
                    "document_count": vector_count
                },
                "cache": {
                    "memory_usage": cache_memory
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取统计信息失败")
