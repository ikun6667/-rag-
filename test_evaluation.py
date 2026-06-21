"""
综合评估测试脚本
测试 RAG 召回率和 MCP 工具调用成功率
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rag.data_processor import data_processor
from app.rag.evaluation import recall_evaluator
from app.mcp.evaluation import tool_evaluator
from app.mcp.e2e_evaluation import e2e_evaluator
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_rag_recall():
    """测试 RAG 召回率"""
    print("\n" + "="*80)
    print("第一部分：RAG 召回率评估")
    print("="*80)
    
    try:
        # 步骤 1: 处理知识库数据
        print("\n[步骤 1] 处理知识库数据...")
        knowledge_dir = "data/knowledge"
        
        if not os.path.exists(knowledge_dir):
            print(f"错误: 知识库目录 {knowledge_dir} 不存在")
            return None
        
        stats = data_processor.process_pipeline(knowledge_dir, rebuild_index=True)
        
        print(f"\n数据处理统计:")
        print(f"  - 加载文档数:        {stats['total_loaded']}")
        print(f"  - 清洗后文档数:      {stats['after_cleaning']}")
        print(f"  - 去重后文档数:      {stats['after_deduplication']}")
        print(f"  - 分块总数:          {stats['total_chunks']}")
        
        # 步骤 2: 执行召回率评估
        print("\n[步骤 2] 执行召回率评估...")
        recall_evaluator.load_test_dataset()
        results = recall_evaluator.evaluate(top_k=5)
        
        # 步骤 3: 保存结果
        print("\n[步骤 3] 保存评估结果...")
        recall_evaluator.save_results(results, "rag_evaluation_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"RAG 召回率测试失败: {e}", exc_info=True)
        return None


async def test_tool_call_success_rate():
    """测试工具调用成功率（单一工具测试）"""
    print("\n" + "="*80)
    print("第二部分：MCP 单一工具调用成功率评估")
    print("="*80)
    
    try:
        # 步骤 1: 加载测试用例
        print("\n[步骤 1] 加载测试用例...")
        tool_evaluator.load_test_cases()
        
        # 步骤 2: 执行工具调用测试
        print("\n[步骤 2] 执行工具调用测试...")
        results = await tool_evaluator.evaluate_all()
        
        # 步骤 3: 保存结果
        print("\n[步骤 3] 保存评估结果...")
        tool_evaluator.save_results(results, "tool_evaluation_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"工具调用测试失败: {e}", exc_info=True)
        return None


async def test_e2e_tool_selection():
    """测试端到端工具选择成功率（基于 Workflow 自然语言交互）"""
    print("\n" + "="*80)
    print("第三部分：端到端工具选择成功率评估（Workflow 自然语言交互）")
    print("="*80)
    
    try:
        # 步骤 1: 加载测试用例
        print("\n[步骤 1] 加载端到端测试用例...")
        e2e_evaluator.load_test_cases()
        
        # 步骤 2: 执行端到端测试
        print("\n[步骤 2] 执行端到端工具选择测试...")
        results = await e2e_evaluator.evaluate_all()
        
        # 步骤 3: 保存结果
        print("\n[步骤 3] 保存评估结果...")
        e2e_evaluator.save_results(results, "e2e_tool_evaluation_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"端到端测试失败: {e}", exc_info=True)
        return None


def print_summary(rag_results, tool_results, e2e_results):
    """打印总体总结"""
    print("\n" + "="*80)
    print("总体评估总结")
    print("="*80)
    
    if rag_results:
        print("\n📊 RAG 召回率评估:")
        print(f"  - 平均 Recall@5:     {rag_results['avg_recall']:.4f}")
        print(f"  - 平均 Precision@5:  {rag_results['avg_precision']:.4f}")
        print(f"  - MRR:               {rag_results['mrr']:.4f}")
        print(f"  - 测试查询数:        {rag_results['num_queries']}")
    
    if tool_results:
        print("\n🔧 MCP 单一工具调用评估:")
        print(f"  - 总测试数:          {tool_results['total_tests']}")
        print(f"  - 成功数:            {tool_results['success_count']}")
        print(f"  - 失败数:            {tool_results['failed_count']}")
        print(f"  - 成功率:            {tool_results['success_rate']:.2f}%")
        print(f"  - 平均响应时间:      {tool_results['avg_response_time']:.2f}s")
    
    if e2e_results:
        print("\n🎯 端到端工具选择评估（Workflow 自然语言交互）:")
        print(f"  - 总测试数:          {e2e_results['total_tests']}")
        print(f"  - 完全成功数:        {e2e_results['success_count']}")
        print(f"  - 失败数:            {e2e_results['failed_count']}")
        print(f"  - 总体成功率:        {e2e_results['success_rate']:.2f}%")
        print(f"  - Agent 选择准确率:  {e2e_results['agent_selection_accuracy']:.2f}%")
        print(f"  - 路由正确率:        {e2e_results['routing_accuracy']:.2f}%")
        print(f"  - 平均响应时间:      {e2e_results['avg_response_time']:.2f}s")
    
    print("\n" + "="*80)
    print("✅ 所有评估完成！")
    print("="*80 + "\n")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("旅游规划系统 - 综合评估测试")
    print("="*80)
    
    # 测试 RAG 召回率
    rag_results = test_rag_recall()
    
    # 测试单一工具调用成功率（异步）
    tool_results = asyncio.run(test_tool_call_success_rate())
    
    # 测试端到端工具选择成功率（异步）
    e2e_results = asyncio.run(test_e2e_tool_selection())
    
    # 打印总结
    print_summary(rag_results, tool_results, e2e_results)
    
    return rag_results, tool_results, e2e_results


if __name__ == "__main__":
    main()
