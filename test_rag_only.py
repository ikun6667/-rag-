"""
单独测试 RAG 召回率 - 低内存版本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rag.data_processor import data_processor
from app.rag.evaluation import recall_evaluator
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("="*80)
    print("RAG 召回率评估")
    print("="*80)
    
    # 处理数据
    print("\n[步骤 1] 处理知识库数据...")
    stats = data_processor.process_pipeline("data/knowledge", rebuild_index=True)
    print(f"数据处理完成: {stats}")
    
    # 执行评估
    print("\n[步骤 2] 执行召回率评估...")
    recall_evaluator.load_test_dataset()
    results = recall_evaluator.evaluate(top_k=5)
    
    # 保存结果
    print("\n[步骤 3] 保存结果...")
    recall_evaluator.save_results(results, "rag_evaluation_results.json")
    
    print("\n✅ RAG 评估完成!")

if __name__ == "__main__":
    main()
