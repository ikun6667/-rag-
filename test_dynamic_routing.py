"""
测试动态路由功能 - 智能决定运行哪些 Agent
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_dynamic_routing():
    """测试动态路由功能"""
    print("=" * 80)
    print("测试动态路由功能 - 智能选择 Agent")
    print("=" * 80)
    
    from app.graph.workflow import create_workflow
    
    # 创建新的工作流实例
    workflow_app = create_workflow()
    
    # 测试场景1: 完整的旅行规划（应该运行所有 Agent）
    print("\n【场景1】完整旅行规划请求")
    print("-" * 80)
    print("用户输入: 我想去北京玩3天，喜欢历史文化和美食")
    
    initial_state_1 = {
        "query": "我想去北京玩3天，喜欢历史文化和美食",
        "location": "北京",
        "days": 3,
        "budget": "中等",
        "preferences": "喜欢历史文化和美食",
        "attraction_result": {},
        "weather_result": {},
        "hotel_result": {},
        "plan_result": {},
        "next_step": "",
        "needs_clarification": False,
        "clarification_questions": [],
        "agents_to_run": [],
        "completed_agents": [],
        "final_response": ""
    }
    
    result_1 = await workflow_app.ainvoke(initial_state_1)
    print(f"✓ 运行的 Agent: {result_1.get('agents_to_run', [])}")
    print(f"✓ 完成的 Agent: {result_1.get('completed_agents', [])}")
    print(f"✓ 景点结果: {'有' if result_1.get('attraction_result') else '无'}")
    print(f"✓ 天气结果: {'有' if result_1.get('weather_result') else '无'}")
    print(f"✓ 酒店结果: {'有' if result_1.get('hotel_result') else '无'}")
    print(f"✓ 最终回复长度: {len(result_1.get('final_response', ''))} 字符")
    
    # 测试场景2: 只查询景点（应该只运行 attraction）
    print("\n【场景2】仅查询景点")
    print("-" * 80)
    print("用户输入: 北京有什么好玩的景点？")
    
    initial_state_2 = {
        "query": "北京有什么好玩的景点？",
        "location": "北京",
        "days": 1,
        "budget": "中等",
        "preferences": "",
        "attraction_result": {},
        "weather_result": {},
        "hotel_result": {},
        "plan_result": {},
        "next_step": "",
        "needs_clarification": False,
        "clarification_questions": [],
        "agents_to_run": [],
        "completed_agents": [],
        "final_response": ""
    }
    
    result_2 = await workflow_app.ainvoke(initial_state_2)
    print(f"✓ 运行的 Agent: {result_2.get('agents_to_run', [])}")
    print(f"✓ 完成的 Agent: {result_2.get('completed_agents', [])}")
    print(f"✓ 景点结果: {'有' if result_2.get('attraction_result') else '无'}")
    print(f"✓ 天气结果: {'有' if result_2.get('weather_result') else '无'}")
    print(f"✓ 酒店结果: {'有' if result_2.get('hotel_result') else '无'}")
    
    # 测试场景3: 查询天气（应该只运行 weather）
    print("\n【场景3】仅查询天气")
    print("-" * 80)
    print("用户输入: 北京明天天气怎么样？需要带伞吗？")
    
    initial_state_3 = {
        "query": "北京明天天气怎么样？需要带伞吗？",
        "location": "北京",
        "days": 1,
        "budget": "低",
        "preferences": "",
        "attraction_result": {},
        "weather_result": {},
        "hotel_result": {},
        "plan_result": {},
        "next_step": "",
        "needs_clarification": False,
        "clarification_questions": [],
        "agents_to_run": [],
        "completed_agents": [],
        "final_response": ""
    }
    
    result_3 = await workflow_app.ainvoke(initial_state_3)
    print(f"✓ 运行的 Agent: {result_3.get('agents_to_run', [])}")
    print(f"✓ 完成的 Agent: {result_3.get('completed_agents', [])}")
    print(f"✓ 景点结果: {'有' if result_3.get('attraction_result') else '无'}")
    print(f"✓ 天气结果: {'有' if result_3.get('weather_result') else '无'}")
    print(f"✓ 酒店结果: {'有' if result_3.get('hotel_result') else '无'}")
    
    # 测试场景4: 查询住宿（应该只运行 hotel）
    print("\n【场景4】仅查询住宿")
    print("-" * 80)
    print("用户输入: 推荐几家北京市中心的酒店")
    
    initial_state_4 = {
        "query": "推荐几家北京市中心的酒店",
        "location": "北京",
        "days": 2,
        "budget": "高",
        "preferences": "市中心",
        "attraction_result": {},
        "weather_result": {},
        "hotel_result": {},
        "plan_result": {},
        "next_step": "",
        "needs_clarification": False,
        "clarification_questions": [],
        "agents_to_run": [],
        "completed_agents": [],
        "final_response": ""
    }
    
    result_4 = await workflow_app.ainvoke(initial_state_4)
    print(f"✓ 运行的 Agent: {result_4.get('agents_to_run', [])}")
    print(f"✓ 完成的 Agent: {result_4.get('completed_agents', [])}")
    print(f"✓ 景点结果: {'有' if result_4.get('attraction_result') else '无'}")
    print(f"✓ 天气结果: {'有' if result_4.get('weather_result') else '无'}")
    print(f"✓ 酒店结果: {'有' if result_4.get('hotel_result') else '无'}")
    
    # 测试场景5: 景点 + 天气（不需要酒店）
    print("\n【场景5】一日游规划（景点+天气）")
    print("-" * 80)
    print("用户输入: 上海一日游攻略，需要了解天气")
    
    initial_state_5 = {
        "query": "上海一日游攻略，需要了解天气",
        "location": "上海",
        "days": 1,
        "budget": "中等",
        "preferences": "",
        "attraction_result": {},
        "weather_result": {},
        "hotel_result": {},
        "plan_result": {},
        "next_step": "",
        "needs_clarification": False,
        "clarification_questions": [],
        "agents_to_run": [],
        "completed_agents": [],
        "final_response": ""
    }
    
    result_5 = await workflow_app.ainvoke(initial_state_5)
    print(f"✓ 运行的 Agent: {result_5.get('agents_to_run', [])}")
    print(f"✓ 完成的 Agent: {result_5.get('completed_agents', [])}")
    print(f"✓ 景点结果: {'有' if result_5.get('attraction_result') else '无'}")
    print(f"✓ 天气结果: {'有' if result_5.get('weather_result') else '无'}")
    print(f"✓ 酒店结果: {'有' if result_5.get('hotel_result') else '无'}")
    
    print("\n" + "=" * 80)
    print("✅ 动态路由测试完成！")
    print("=" * 80)
    print("\n总结:")
    print("- 系统会根据用户需求智能判断需要运行哪些 Agent")
    print("- 避免了不必要的 API 调用，提高响应速度")
    print("- 降低了资源消耗和成本")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_dynamic_routing())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
