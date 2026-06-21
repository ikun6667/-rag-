"""
Rerank 重排序模块
"""
import os
# 禁用代理，直连网络
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

from sentence_transformers import CrossEncoder
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class Reranker:
    """重排序器"""
    
    def __init__(self, model_name: str = None):
        # 使用本地模型路径，避免联网检查
        if model_name is None:
            model_name = os.path.expanduser("~/.cache/huggingface/hub/models--BAAI--bge-reranker-v2-m3/snapshots/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e")
        
        self.model = CrossEncoder(model_name)
        logger.info(f"Reranker initialized with model: {model_name}")
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        对检索结果进行重排序
        """
        if not documents:
            return []
        
        # 准备输入
        pairs = [[query, doc['document']] for doc in documents]
        
        # 计算相关性分数
        scores = self.model.predict(pairs)
        
        # 添加分数到结果
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)
        
        # 按分数排序
        ranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
        
        # 返回 Top-K
        return ranked_docs[:top_k]


# 全局重排序器实例
reranker = Reranker()
