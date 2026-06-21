"""
快速重建 RAG 索引
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 禁用 ChromaDB 遥测（避免兼容性警告）
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 加载环境变量（从 .env 文件）
from dotenv import load_dotenv
load_dotenv()

from app.rag.data_processor import data_processor

def rebuild_index():
    print("="*80)
    print("重建 RAG 索引")
    print("="*80)
    
    knowledge_dir = "data/knowledge"
    
    if not os.path.exists(knowledge_dir):
        print(f"❌ 知识库目录 {knowledge_dir} 不存在")
        return
    
    print("\n开始处理知识库数据...")
    stats = data_processor.process_pipeline(knowledge_dir, rebuild_index=True)
    
    print(f"\n✅ 索引重建完成！")
    print(f"\n数据统计:")
    print(f"  - 加载文档数:        {stats['total_loaded']}")
    print(f"  - 清洗后文档数:      {stats['after_cleaning']}")
    print(f"  - 去重后文档数:      {stats['after_deduplication']}")
    print(f"  - 分块总数:          {stats['total_chunks']}")
    
    # 验证索引
    from app.rag.retriever import hybrid_retriever
    from app.rag.vector_store import vector_store
    
    print(f"\n索引状态:")
    print(f"  - 向量库文档数:      {vector_store.count()}")
    print(f"  - BM25 索引:         {'✓ 已构建' if hybrid_retriever.bm25 else '✗ 未构建'}")
    print(f"  - BM25 语料库大小:   {len(hybrid_retriever.corpus)}")
    
    # 快速测试
    print(f"\n快速测试检索...")
    test_query = "北京故宫"
    results = hybrid_retriever.hybrid_search(test_query, top_k=2)
    print(f"查询 '{test_query}' 返回 {len(results)} 个结果")
    
    if results:
        print(f"  [1] Score: {results[0].get('rrf_score', results[0].get('score', 0)):.4f}")
        print(f"      Content: {results[0]['document'][:100]}...")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    rebuild_index()
