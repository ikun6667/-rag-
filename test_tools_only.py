"""
单独测试工具调用 - 低内存版本(不需要 LLM)
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.mcp.evaluation import tool_evaluator
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    print("="*80)
    print("MCP 工具调用成功率评估")
    print("="*80)
    
    # 加载测试用例
    print("\n[步骤 1] 加载测试用例...")
    tool_evaluator.load_test_cases()
    
    # 执行测试
    print("\n[步骤 2] 执行工具调用测试...")
    results = await tool_evaluator.evaluate_all()
    
    # 保存结果
    print("\n[步骤 3] 保存结果...")
    tool_evaluator.save_results(results, "tool_evaluation_results.json")
    
    print("\n✅ 工具调用评估完成!")

if __name__ == "__main__":
    asyncio.run(main())
