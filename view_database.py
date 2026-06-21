"""
查看 ChromaDB 向量数据库内容
"""
import os
from app.core.database import chroma_client
from app.core.config import settings

# 禁用遥测
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def view_collection(collection_name="travel_knowledge"):
    """查看集合内容"""
    print("="*80)
    print(f"查看向量数据库: {collection_name}")
    print("="*80)
    
    try:
        # 获取集合
        collection = chroma_client.get_collection(name=collection_name)
        
        # 获取所有数据
        results = collection.get(
            include=['documents', 'metadatas', 'embeddings']
        )
        
        total_count = len(results['ids'])
        print(f"\n📊 总文档数: {total_count}\n")
        
        if total_count == 0:
            print("⚠️  数据库为空，请先运行 rebuild_rag_index.py 构建索引")
            return
        
        # 显示每个文档的详细信息
        for i, (doc_id, document, metadata) in enumerate(
            zip(results['ids'], results['documents'], results['metadatas']), 1
        ):
            print(f"{'─'*80}")
            print(f"文档 #{i}")
            print(f"  ID:       {doc_id}")
            print(f"  元数据:   {metadata}")
            print(f"  内容长度: {len(document)} 字符")
            print(f"  内容预览: {document[:200]}...")
            print()
        
        # 统计信息
        print(f"{'='*80}")
        print("📈 统计信息:")
        print(f"  - 总文档数: {total_count}")
        
        # 按元数据统计
        source_counts = {}
        for meta in results['metadatas']:
            source = meta.get('source_idx', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print(f"  - 来源分布: {len(source_counts)} 个源文件")
        for source, count in sorted(source_counts.items()):
            print(f"    · 源文件 #{source}: {count} 个分块")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"提示: 可能需要先运行 python rebuild_rag_index.py 构建索引")

if __name__ == "__main__":
    view_collection()
