"""
向量存储与索引 - ChromaDB
"""
import os
# 禁用代理，直连网络
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

from app.core.database import chroma_client
from app.core.config import settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, collection_name: str = "travel_knowledge"):
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # 创建或获取集合
        try:
            self.collection = chroma_client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[str], 
                     metadatas: Optional[List[Dict]] = None,
                     ids: Optional[List[str]] = None):
        """添加文档到向量库"""
        # 生成 embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # 生成 ID（如果未提供）
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # 生成元数据
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]
        
        # 添加到集合
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, top_k: int = None, 
               where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        # 生成查询向量
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # 搜索
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def delete(self, ids: List[str]):
        """删除文档"""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents")
    
    def count(self) -> int:
        """获取文档数量"""
        return self.collection.count()
    
    def clear(self):
        """清空集合"""
        try:
            chroma_client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception:
            logger.warning(f"Collection {self.collection_name} does not exist")
        
        # 重新创建空集合
        self.collection = chroma_client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Recreated empty collection: {self.collection_name}")


# 全局向量存储实例
vector_store = VectorStore()
