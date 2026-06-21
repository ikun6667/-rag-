"""
混合检索系统 - BM25 + BGE-M3 + RRF 融合
"""
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from app.rag.vector_store import vector_store
from app.core.config import settings
from typing import List, Dict, Any
import jieba
import numpy as np
import logging

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器"""
    
    def __init__(self):
        self.bm25 = None
        self.corpus = []
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.documents_map = {}
    
    def build_index(self, documents: List[str]):
        """构建检索索引"""
        self.corpus = documents
        
        # 构建 BM25 索引
        tokenized_corpus = [list(jieba.cut(doc)) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # 构建文档映射
        self.documents_map = {i: doc for i, doc in enumerate(documents)}

        logger.info(f"Built hybrid index with {len(documents)} documents")
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """BM25 检索"""
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index first.")
        
        # 分词
        query_tokens = list(jieba.cut(query))
        
        # 获取分数
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取 Top-K
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'index': int(idx),
                    'document': self.documents_map[idx],
                    'score': float(scores[idx]),
                    'method': 'bm25'
                })
        
        return results
    
    def vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """向量检索（使用 BGE-M3）"""
        results = vector_store.search(query, top_k=top_k)
        
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                'index': i,
                'document': result['document'],
                'score': 1 - result['distance'],  # 转换为相似度
                'method': 'vector',
                'metadata': result['metadata']
            })
        
        return formatted_results
    
    def rrf_fusion(self, bm25_results: List[Dict], 
                   vector_results: List[Dict], 
                   k: int = None) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        """
        if k is None:
            k = settings.RRF_K_VALUE
        
        # 收集所有文档
        all_docs = {}
        
        # 处理 BM25 结果
        for rank, result in enumerate(bm25_results, 1):
            doc_id = result['document']
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    'document': doc_id,
                    'rrf_score': 0,
                    'bm25_rank': rank,
                    'vector_rank': None,
                    'metadata': result.get('metadata', {})
                }
            all_docs[doc_id]['rrf_score'] += 1 / (k + rank)
            all_docs[doc_id]['bm25_rank'] = rank
        
        # 处理向量检索结果
        for rank, result in enumerate(vector_results, 1):
            doc_id = result['document']
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    'document': doc_id,
                    'rrf_score': 0,
                    'bm25_rank': None,
                    'vector_rank': rank,
                    'metadata': result.get('metadata', {})
                }
            all_docs[doc_id]['rrf_score'] += 1 / (k + rank)
            all_docs[doc_id]['vector_rank'] = rank
        
        # 按 RRF 分数排序
        sorted_results = sorted(
            all_docs.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )
        
        return sorted_results
    
    def hybrid_search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        执行混合检索
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        # 如果 BM25 索引未构建，仅使用向量检索
        if self.bm25 is None:
            logger.warning("BM25 index not built, falling back to vector search only")
            return self.vector_search(query, top_k=top_k)
        
        # BM25 检索（召回更多候选）
        bm25_results = self.bm25_search(query, top_k=top_k * 2)
        
        # 向量检索
        vector_results = self.vector_search(query, top_k=top_k * 2)
        
        # RRF 融合
        fused_results = self.rrf_fusion(bm25_results, vector_results)
        
        # 返回 Top-K
        return fused_results[:top_k]


# 全局检索器实例
hybrid_retriever = HybridRetriever()
