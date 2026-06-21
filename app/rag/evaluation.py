"""
RAG 召回率评估工具
用于测试检索系统的相关性和召回质量
"""
import json
from typing import List, Dict, Any
from app.rag.retriever import hybrid_retriever
from app.rag.data_processor import data_processor
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RecallEvaluator:
    """召回率评估器"""
    
    def __init__(self):
        self.test_queries = []
        self.ground_truth = {}
    
    def load_test_dataset(self, dataset_path: str = None):
        """
        加载测试数据集
        
        Args:
            dataset_path: 测试数据集JSON文件路径，如果为None则使用默认测试集
        """
        if dataset_path:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_queries = data.get('queries', [])
                self.ground_truth = {item['query']: item['relevant_docs'] 
                                   for item in data.get('ground_truth', [])}
        else:
            # 使用默认测试集
            self.test_queries = [
                "北京故宫的开放时间和门票价格",
                "上海外滩有什么特色建筑",
                "成都宽窄巷子的美食推荐",
                "杭州西湖十景有哪些",
                "西安兵马俑的一号坑有什么特点",
                "故宫博物院的游览路线",
                "外滩附近的购物场所",
                "宽窄巷子的交通方式",
                "西湖的最佳旅游季节",
                "兵马俑周边的景点"
            ]
            
            #  ground truth 定义（相关文档索引）
            self.ground_truth = {
                "北京故宫的开放时间和门票价格": [0],
                "上海外滩有什么特色建筑": [1],
                "成都宽窄巷子的美食推荐": [2],
                "杭州西湖十景有哪些": [3],
                "西安兵马俑的一号坑有什么特点": [4],
                "故宫博物院的游览路线": [0],
                "外滩附近的购物场所": [1],
                "宽窄巷子的交通方式": [2],
                "西湖的最佳旅游季节": [3],
                "兵马俑周边的景点": [4]
            }
        
        logger.info(f"Loaded {len(self.test_queries)} test queries")
    
    def calculate_recall_at_k(self, query: str, retrieved_docs: List[Dict], 
                              k: int = 5) -> float:
        """
        计算单个查询的 Recall@K
        
        Args:
            query: 查询文本
            retrieved_docs: 检索返回的文档列表
            k: 评估的Top-K值
            
        Returns:
            Recall@K 值 (0-1)
        """
        if not retrieved_docs:
            return 0.0
        
        # 提取查询中的关键实体词
        import jieba
        query_keywords = [word for word in jieba.cut(query) 
                         if len(word.strip()) > 1 
                         and word.strip() not in ['的', '有', '什么', '哪些', '是', '和', '与', '及']]
        
        if not query_keywords:
            return 0.0
        
        # 统计有多少个关键词在检索结果中出现
        matched_keywords = set()
        for doc in retrieved_docs[:k]:
            doc_text = doc.get('document', '').lower()
            
            for keyword in query_keywords:
                if keyword.lower() in doc_text:
                    matched_keywords.add(keyword)
        
        # 召回率 = 匹配的关键词数 / 总关键词数
        recall = len(matched_keywords) / len(query_keywords)
        return min(recall, 1.0)
    
    def calculate_precision_at_k(self, query: str, retrieved_docs: List[Dict], 
                                 k: int = 5) -> float:
        """
        计算单个查询的 Precision@K
        
        Args:
            query: 查询文本
            retrieved_docs: 检索返回的文档列表
            k: 评估的Top-K值
            
        Returns:
            Precision@K 值 (0-1)
        """
        if not retrieved_docs:
            return 0.0
        
        # 提取查询中的关键实体词
        import jieba
        query_keywords = [word for word in jieba.cut(query) 
                         if len(word.strip()) > 1 
                         and word.strip() not in ['的', '有', '什么', '哪些', '是', '和', '与', '及']]
        
        if not query_keywords:
            return 0.0
        
        # 统计相关文档数量（包含至少一个关键词的文档）
        relevant_count = 0
        for doc in retrieved_docs[:k]:
            doc_text = doc.get('document', '').lower()
            
            # 如果文档包含至少一个关键词，认为是相关的
            if any(keyword.lower() in doc_text for keyword in query_keywords):
                relevant_count += 1
        
        # 精确率 = 相关文档数 / 返回的文档总数
        precision = relevant_count / min(k, len(retrieved_docs))
        return precision
    
    def calculate_mrr(self, all_results: List[Dict[str, Any]]) -> float:
        """
        计算平均倒数排名 (Mean Reciprocal Rank)
        
        Args:
            all_results: 所有查询的检索结果列表
            
        Returns:
            MRR 值 (0-1)
        """
        import jieba
        reciprocal_ranks = []
        
        for result in all_results:
            query = result['query']
            retrieved_docs = result['retrieved_docs']
            
            # 提取查询关键词
            query_keywords = [word for word in jieba.cut(query) 
                             if len(word.strip()) > 1 
                             and word.strip() not in ['的', '有', '什么', '哪些', '是', '和', '与', '及']]
            
            if not query_keywords:
                reciprocal_ranks.append(0.0)
                continue
            
            # 找到第一个相关文档的位置
            rank = None
            for i, doc in enumerate(retrieved_docs, 1):
                doc_text = doc.get('document', '').lower()
                
                # 如果文档包含至少一个关键词，认为是相关的
                if any(keyword.lower() in doc_text for keyword in query_keywords):
                    rank = i
                    break
            
            if rank is not None:
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)
        
        if not reciprocal_ranks:
            return 0.0
        
        return sum(reciprocal_ranks) / len(reciprocal_ranks)
    
    def evaluate(self, top_k: int = 5) -> Dict[str, float]:
        """
        执行完整的召回率评估
        
        Args:
            top_k: 评估的Top-K值
            
        Returns:
            评估结果字典
        """
        if not self.test_queries:
            raise ValueError("No test queries loaded. Call load_test_dataset first.")
        
        results = []
        recall_scores = []
        precision_scores = []
        
        print(f"\n{'='*60}")
        print(f"开始 RAG 召回率评估 (Top-{top_k})")
        print(f"{'='*60}\n")
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n[{i}/{len(self.test_queries)}] 查询: {query}")
            
            # 执行检索
            retrieved_docs = hybrid_retriever.hybrid_search(query, top_k=top_k)
            
            # 调试信息：显示检索到的文档内容预览
            if retrieved_docs:
                print(f"  - 检索到 {len(retrieved_docs)} 个文档")
                for j, doc in enumerate(retrieved_docs[:2], 1):  # 只显示前2个
                    doc_preview = doc.get('document', '')[:100]
                    score = doc.get('rrf_score', doc.get('score', 'N/A'))
                    print(f"    [{j}] Score: {score:.4f} | Content: {doc_preview}...")
            else:
                print(f"  - ⚠️ 未检索到任何文档！")
            
            # 计算指标
            recall = self.calculate_recall_at_k(query, retrieved_docs, top_k)
            precision = self.calculate_precision_at_k(query, retrieved_docs, top_k)
            
            recall_scores.append(recall)
            precision_scores.append(precision)
            
            results.append({
                'query': query,
                'retrieved_docs': retrieved_docs,
                'recall': recall,
                'precision': precision
            })
            
            print(f"  - Recall@{top_k}: {recall:.4f}")
            print(f"  - Precision@{top_k}: {precision:.4f}")
        
        # 计算平均指标
        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0
        mrr = self.calculate_mrr(results)
        
        # 输出总结
        print(f"\n{'='*60}")
        print(f"评估结果总结")
        print(f"{'='*60}")
        print(f"平均 Recall@{top_k}:     {avg_recall:.4f}")
        print(f"平均 Precision@{top_k}:  {avg_precision:.4f}")
        print(f"MRR (平均倒数排名):      {mrr:.4f}")
        print(f"测试查询数量:            {len(self.test_queries)}")
        print(f"{'='*60}\n")
        
        return {
            'avg_recall': avg_recall,
            'avg_precision': avg_precision,
            'mrr': mrr,
            'num_queries': len(self.test_queries),
            'detailed_results': results
        }
    
    def save_results(self, results: Dict[str, Any], output_path: str = "rag_evaluation_results.json"):
        """
        保存评估结果到文件
        
        Args:
            results: 评估结果字典
            output_path: 输出文件路径
        """
        # 序列化结果（移除不可序列化的内容）
        serializable_results = {
            'avg_recall': results['avg_recall'],
            'avg_precision': results['avg_precision'],
            'mrr': results['mrr'],
            'num_queries': results['num_queries'],
            'detailed_results': [
                {
                    'query': r['query'],
                    'recall': r['recall'],
                    'precision': r['precision'],
                    'num_retrieved': len(r['retrieved_docs'])
                }
                for r in results['detailed_results']
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        print(f"\n评估结果已保存到: {output_path}")


# 全局评估器实例
recall_evaluator = RecallEvaluator()
