"""
RAG 调试脚本 - 检查检索系统是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rag.data_processor import data_processor
from app.rag.retriever import hybrid_retriever
from app.rag.vector_store import vector_store

def test_rag_system():
    print("="*80)
    print("RAG 系统诊断测试")
    print("="*80)
    
    # 1. 检查向量库中的文档数量
    print("\n[步骤 1] 检查向量库状态...")
    doc_count = vector_store.count()
    print(f"向量库中文档数量: {doc_count}")
    
    if doc_count == 0:
        print("⚠️ 向量库为空！需要先处理知识库数据")
        print("\n[步骤 2] 处理知识库数据...")
        knowledge_dir = "data/knowledge"
        
        if not os.path.exists(knowledge_dir):
            print(f"❌ 知识库目录 {knowledge_dir} 不存在")
            return
        
        stats = data_processor.process_pipeline(knowledge_dir, rebuild_index=True)
        print(f"\n数据处理统计:")
        print(f"  - 加载文档数:        {stats['total_loaded']}")
        print(f"  - 清洗后文档数:      {stats['after_cleaning']}")
        print(f"  - 去重后文档数:      {stats['after_deduplication']}")
        print(f"  - 分块总数:          {stats['total_chunks']}")
        
        # 重新检查文档数量
        doc_count = vector_store.count()
        print(f"\n处理后向量库中文档数量: {doc_count}")
    else:
        print("✓ 向量库已有数据，检查是否需要重建 BM25 索引")
    
    # 2. 测试混合检索器状态
    print("\n[步骤 3] 检查混合检索器状态...")
    print(f"BM25 索引是否构建: {hybrid_retriever.bm25 is not None}")
    print(f"语料库大小: {len(hybrid_retriever.corpus)}")
    print(f"文档映射大小: {len(hybrid_retriever.documents_map)}")
    
    if not hybrid_retriever.bm25 or len(hybrid_retriever.corpus) == 0:
        print("⚠️ BM25 索引未构建或语料库为空，需要重新构建")
        # 从向量库获取所有文档来构建 BM25 索引
        print("尝试重新构建 BM25 索引...")
        try:
            # 需要从数据源重新加载文本来构建 BM25 索引
            knowledge_dir = "data/knowledge"
            if os.path.exists(knowledge_dir):
                print("重新处理知识库以构建完整的混合检索索引...")
                stats = data_processor.process_pipeline(knowledge_dir, rebuild_index=False)
                print(f"✓ BM25 索引已构建，包含 {len(hybrid_retriever.corpus)} 个文档")
            else:
                print(f"❌ 知识库目录 {knowledge_dir} 不存在")
        except Exception as e:
            print(f"❌ 构建 BM25 索引失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"✓ BM25 索引已就绪，包含 {len(hybrid_retriever.corpus)} 个文档")
    
    # 3. 执行测试查询
    print("\n[步骤 4] 执行测试查询...")
    test_queries = [
        "北京故宫",
        "上海外滩",
        "西湖"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        # 测试 BM25 检索
        try:
            bm25_results = hybrid_retriever.bm25_search(query, top_k=3)
            print(f"  BM25 检索结果: {len(bm25_results)} 个")
            if bm25_results:
                for i, result in enumerate(bm25_results[:1], 1):
                    print(f"    [{i}] Score: {result['score']:.4f}")
                    print(f"        Content: {result['document'][:100]}...")
        except Exception as e:
            print(f"  ❌ BM25 检索失败: {e}")
        
        # 测试向量检索
        try:
            vector_results = hybrid_retriever.vector_search(query, top_k=3)
            print(f"  向量检索结果: {len(vector_results)} 个")
            if vector_results:
                for i, result in enumerate(vector_results[:1], 1):
                    print(f"    [{i}] Score: {result['score']:.4f}")
                    print(f"        Content: {result['document'][:100]}...")
        except Exception as e:
            print(f"  ❌ 向量检索失败: {e}")
        
        # 测试混合检索
        try:
            hybrid_results = hybrid_retriever.hybrid_search(query, top_k=3)
            print(f"  混合检索结果: {len(hybrid_results)} 个")
            if hybrid_results:
                for i, result in enumerate(hybrid_results[:2], 1):
                    score = result.get('rrf_score', result.get('score', 0))
                    print(f"    [{i}] Score: {score:.4f}")
                    print(f"        Content: {result['document'][:100]}...")
        except Exception as e:
            print(f"  ❌ 混合检索失败: {e}")
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)

if __name__ == "__main__":
    test_rag_system()
