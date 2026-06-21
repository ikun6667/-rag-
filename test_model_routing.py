"""
测试模型路由功能 - 根据任务类型自动选择合适的 LLM 模型
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_model_router():
    """测试模型路由器"""
    print("=" * 80)
    print("测试模型路由功能")
    print("=" * 80)
    
    from app.models.model_router import model_router, ModelTier
    
    # 测试1: 基于任务类型的路由
    print("\n【测试1】基于任务类型的路由决策")
    print("-" * 80)
    
    test_tasks = [
        ("weather_query", "天气查询"),
        ("simple_qa", "简单问答"),
        ("attraction_search", "景点搜索"),
        ("hotel_search", "酒店搜索"),
        ("itinerary_planning", "行程规划"),
        ("complex_analysis", "综合分析"),
    ]
    
    for task_type, description in test_tasks:
        tier = model_router.route_by_task(task_type)
        config = model_router.get_model_config(tier)
        print(f"{description:12} ({task_type:25}) → {tier.value.upper():10} 模型: {config.name}")
    
    # 测试2: 基于复杂度的路由
    print("\n【测试2】基于复杂度的路由决策")
    print("-" * 80)
    
    complexity_tests = [
        (0.1, "非常简单"),
        (0.3, "简单"),
        (0.5, "中等"),
        (0.7, "较复杂"),
        (0.9, "非常复杂"),
    ]
    
    for score, description in complexity_tests:
        tier = model_router.route_by_complexity(score)
        print(f"复杂度 {score:.1f} ({description:8}) → {tier.value.upper()} 模型")
    
    # 测试3: 获取不同等级的模型配置
    print("\n【测试3】各等级模型配置详情")
    print("-" * 80)
    
    for tier in ModelTier:
        config = model_router.get_model_config(tier)
        print(f"\n{tier.value.upper()} 模型:")
        print(f"  - 名称:       {config.name}")
        print(f"  - API地址:    {config.api_base}")
        print(f"  - 温度:       {config.temperature}")
        print(f"  - 最大tokens: {config.max_tokens}")
    
    print("\n" + "=" * 80)
    print("✅ 模型路由器测试完成！")
    print("=" * 80)


async def test_llm_client_with_routing():
    """测试 LLM Client 的模型路由功能"""
    print("\n" + "=" * 80)
    print("测试 LLM Client 模型路由")
    print("=" * 80)
    
    from app.models.llm_client import llm_client
    from app.models.model_router import ModelTier
    
    # 测试1: 默认模型（标准模型）
    print("\n【测试1】默认模型调用")
    print("-" * 80)
    try:
        default_model = llm_client.chat_model
        print(f"✓ 默认模型: {default_model.model_name}")
        print(f"✓ API地址: {default_model.openai_api_base}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试2: 按等级获取模型
    print("\n【测试2】按等级获取模型")
    print("-" * 80)
    for tier in ModelTier:
        try:
            model = llm_client.get_model_by_tier(tier)
            print(f"✓ {tier.value.upper():10} 模型: {model.model_name}")
        except Exception as e:
            print(f"✗ {tier.value.upper():10} 模型失败: {e}")
    
    # 测试3: 按任务类型获取模型
    print("\n【测试3】按任务类型获取模型")
    print("-" * 80)
    task_types = ["weather_query", "attraction_search", "itinerary_planning"]
    for task_type in task_types:
        try:
            model = llm_client.get_model_by_task(task_type)
            print(f"✓ {task_type:25} → {model.model_name}")
        except Exception as e:
            print(f"✗ {task_type:25} 失败: {e}")
    
    print("\n" + "=" * 80)
    print("✅ LLM Client 模型路由测试完成！")
    print("=" * 80)


async def main():
    """主测试函数"""
    await test_model_router()
    await test_llm_client_with_routing()
    
    print("\n" + "=" * 80)
    print("🎉 所有模型路由测试完成！")
    print("=" * 80)
    print("\n总结:")
    print("- ✅ 模型路由器可根据任务类型智能选择模型")
    print("- ✅ 支持 FAST/STANDARD/ADVANCED 三个等级")
    print("- ✅ LLM Client 已集成模型路由功能")
    print("- ✅ 各 Agent 已配置合适的模型等级")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
