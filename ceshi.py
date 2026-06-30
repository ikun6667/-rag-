"""
简单本地测试 - 无需启动 API 服务
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_weather():
    """单独测试天气查询"""
    from app.agents.weather_agent import weather_agent

    result = await weather_agent.execute({
        'location': '北京',
        'date': '2026-06-12'
    })
    print(f"状态: {result['status']}")
    print(f"天气: {result.get('weather', {})}")
    print(f"建议: {result.get('suggestion', '')}")


async def test_attraction():
    """单独测试景点推荐"""
    from app.agents.attraction_agent import attraction_agent

    result = await attraction_agent.execute({
        'query': '故宫',
        'location': '北京',
    })
    print(f"状态: {result['status']}")
    print(f"景点数: {len(result.get('attractions', []))}")
    for a in result.get('attractions', [])[:3]:
        print(f"  - {a.get('name', 'N/A')}")


async def test_full_plan():
    """测试完整旅行规划"""
    from app.graph.workflow import create_workflow

    workflow = create_workflow()
    result = await workflow.ainvoke({
        "query": "北京3天旅行计划",
        "location": "北京",
        "days": 3,
        "budget": "中等",
        "preferences": "历史文化",
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
    })
    print(f"最终回复:\n{result.get('final_response', '')}")


if __name__ == "__main__":
    print("=== 测试天气 ===")
    asyncio.run(test_weather())

    # 取消注释来测试其他功能
    print("\n=== 测试景点 ===")
    asyncio.run(test_attraction())

    print("\n=== 测试完整规划 ===")
    asyncio.run(test_full_plan())
