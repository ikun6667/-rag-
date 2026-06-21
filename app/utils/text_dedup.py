"""
文本去重工具 - SimHash + MinHash + TF-IDF 组合策略
"""
import hashlib
import jieba
import numpy as np
from datasketch import MinHash, MinHashLSH
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class TextDeduplicator:
    """文本去重器"""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.minhash_num_perm = 128
        self.tfidf_vectorizer = TfidfVectorizer(tokenizer=self._chinese_tokenizer)
        
    @staticmethod
    def _chinese_tokenizer(text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))
    
    def simhash(self, text: str, hash_size: int = 64) -> int:
        """计算 SimHash"""
        # 分词
        words = self._chinese_tokenizer(text)
        
        # 计算每个词的 hash 值
        v = [0] * hash_size
        for word in words:
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            for i in range(hash_size):
                bitmask = 1 << i
                if h & bitmask:
                    v[i] += 1
                else:
                    v[i] -= 1
        
        # 生成 fingerprint
        fingerprint = 0
        for i in range(hash_size):
            if v[i] > 0:
                fingerprint |= (1 << i)
        
        return fingerprint
    
    def hamming_distance(self, hash1: int, hash2: int, hash_size: int = 64) -> int:
        """计算海明距离"""
        x = hash1 ^ hash2
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance
    
    def minhash_signature(self, text: str) -> MinHash:
        """计算 MinHash 签名"""
        words = self._chinese_tokenizer(text)
        m = MinHash(num_perm=self.minhash_num_perm)
        for word in words:
            m.update(word.encode('utf-8'))
        return m
    
    def tfidf_similarity(self, texts: List[str]) -> np.ndarray:
        """计算 TF-IDF 相似度矩阵"""
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        similarity_matrix = tfidf_matrix.dot(tfidf_matrix.T).toarray()
        return similarity_matrix
    
    def deduplicate(self, texts: List[str]) -> List[int]:
        """
        组合去重策略
        返回唯一文本的索引列表
        """
        n = len(texts)
        if n == 0:
            return []
        
        logger.info(f"Starting deduplication for {n} texts")
        
        # 步骤 1: SimHash 粗筛
        simhashes = [self.simhash(text) for text in texts]
        simhash_candidates = set(range(n))
        
        for i in range(n):
            for j in range(i + 1, n):
                if j not in simhash_candidates:
                    continue
                distance = self.hamming_distance(simhashes[i], simhashes[j])
                if distance <= 3:  # SimHash 阈值
                    simhash_candidates.discard(j)
        
        logger.info(f"After SimHash filtering: {len(simhash_candidates)} candidates")
        
        # 步骤 2: MinHash 精筛
        minhashes = [self.minhash_signature(texts[i]) for i in simhash_candidates]
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.minhash_num_perm)
        
        unique_indices = []
        processed = set()
        
        for idx, (original_idx, mh) in enumerate(zip(simhash_candidates, minhashes)):
            if original_idx in processed:
                continue
            
            unique_indices.append(original_idx)
            processed.add(original_idx)
            
            # 查找相似文档
            similar = lsh.query(mh)
            for sim_idx in similar:
                processed.add(list(simhash_candidates)[sim_idx])
            
            lsh.insert(str(len(unique_indices) - 1), mh)
        
        logger.info(f"After MinHash filtering: {len(unique_indices)} unique texts")
        
        # 步骤 3: TF-IDF 最终验证（对少量候选）
        if len(unique_indices) > 1:
            unique_texts = [texts[i] for i in unique_indices]
            similarity = self.tfidf_similarity(unique_texts)
            
            final_indices = [unique_indices[0]]
            for i in range(1, len(unique_indices)):
                is_duplicate = False
                for j in final_indices:
                    if similarity[i][unique_indices.index(j)] > self.threshold:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    final_indices.append(unique_indices[i])
            
            logger.info(f"Final result: {len(final_indices)} unique texts")
            return final_indices
        
        return unique_indices


# 使用示例
if __name__ == "__main__":
    deduplicator = TextDeduplicator()
    
    # 测试数据
    test_texts = [
        "北京故宫是中国明清两代的皇家宫殿",
        "故宫博物院位于北京市中心，是明清皇宫",
        "上海东方明珠塔是上海的标志性建筑",
        "东方明珠广播电视塔坐落于上海市浦东新区",
        "杭州西湖风景秀丽，闻名中外",
    ]
    
    unique_indices = deduplicator.deduplicate(test_texts)
    print(f"Unique texts indices: {unique_indices}")
    for idx in unique_indices:
        print(f"- {test_texts[idx]}")
