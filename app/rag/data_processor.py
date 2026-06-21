"""
数据处理管道 - 加载、清洗、去重、分块
"""
import os
import json
import pandas as pd
from typing import List, Dict
from app.utils.text_dedup import TextDeduplicator
from app.rag.vector_store import vector_store
from app.rag.retriever import hybrid_retriever
import logging
import re

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.deduplicator = TextDeduplicator(threshold=0.95)  # 提高阈值，减少误删
    
    def load_text_files(self, directory: str) -> List[str]:
        """加载文本文件"""
        texts = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.txt', '.md', '.json')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            if file.endswith('.json'):
                                data = json.load(f)
                                if isinstance(data, list):
                                    texts.extend([item.get('content', '') for item in data])
                                elif isinstance(data, dict):
                                    texts.append(data.get('content', ''))
                            else:
                                content = f.read()
                                texts.append(content)
                    except Exception as e:
                        logger.error(f"Error loading {filepath}: {e}")
        
        logger.info(f"Loaded {len(texts)} documents from {directory}")
        return texts
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除特殊字符（保留中文、英文、数字和常见标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、；：""''（）【】《》\s]', '', text)
        # 去除首尾空白
        text = text.strip()
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 500, 
                   overlap: int = 50) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # 计算本次分块的结束位置
            end = min(start + chunk_size, text_len)
            
            # 尝试在句子边界分割（仅在文本中间时）
            if end < text_len:
                for punct in ['。', '！', '？', '\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 下一次从 start + chunk_size - overlap 开始
            # 这样保证每次前进固定的步长
            next_start = start + chunk_size - overlap
            
            # 但如果已经接近末尾，直接跳到 end
            if next_start >= text_len:
                break
            
            # 确保至少前进了 1 个字符
            if next_start <= start:
                next_start = start + 1
            
            start = next_start
        
        return chunks
    
    def process_pipeline(self, data_dir: str, rebuild_index: bool = True, 
                        batch_size: int = 100):
        """
        完整的数据处理管道（分批处理优化内存）
        """
        logger.info("Starting data processing pipeline...")
        
        # 步骤 1: 加载数据
        raw_texts = self.load_text_files(data_dir)
        logger.info(f"Step 1 - Loaded {len(raw_texts)} raw documents")
        
        # 步骤 2: 清洗
        cleaned_texts = [self.clean_text(text) for text in raw_texts]
        cleaned_texts = [text for text in cleaned_texts if len(text) > 10]
        logger.info(f"Step 2 - Cleaned: {len(cleaned_texts)} documents remain")
        
        # 步骤 3: 去重 (临时禁用，确保所有测试数据入库)
        unique_texts = cleaned_texts
        logger.info(f"Step 3 - Deduplicated: {len(unique_texts)} unique documents (skipped for testing)")
        
        # 步骤 4: 分块 + 步骤 5: 构建索引（分批进行）
        if rebuild_index:
            vector_store.clear()
        
        total_chunks = 0
        all_corpus = []  # 用于 BM25 索引
        
        # 分批处理
        for batch_start in range(0, len(unique_texts), batch_size):
            batch_end = min(batch_start + batch_size, len(unique_texts))
            batch_texts = unique_texts[batch_start:batch_end]
            
            batch_chunks = []
            batch_metadata = []
            
            for idx, text in enumerate(batch_texts):
                actual_idx = batch_start + idx
                chunks = self.chunk_text(text)
                batch_chunks.extend(chunks)
                batch_metadata.extend([{"source_idx": actual_idx}] * len(chunks))
            
            # 添加到向量库
            if batch_chunks:
                vector_store.add_documents(
                    documents=batch_chunks,
                    metadatas=batch_metadata
                )
                all_corpus.extend(batch_chunks)
                total_chunks += len(batch_chunks)
                
                logger.info(f"Processed batch {batch_start//batch_size + 1}: "
                          f"{len(batch_chunks)} chunks added")
            
            # 清理当前批次内存
            del batch_chunks, batch_metadata
        
        logger.info(f"Step 4 - Total chunks: {total_chunks}")
        
        # 构建混合检索索引
        hybrid_retriever.build_index(all_corpus)
        
        logger.info("Data processing pipeline completed!")
        
        return {
            'total_loaded': len(raw_texts),
            'after_cleaning': len(cleaned_texts),
            'after_deduplication': len(unique_texts),
            'total_chunks': total_chunks
        }


# 全局数据处理器
data_processor = DataProcessor()
