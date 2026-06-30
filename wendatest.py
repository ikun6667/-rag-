"""
交互式问答测试 - 模拟真实用户对话
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def ask(query: str, location: str = "北京", days: int = 1):
    """向系统提问"""
    from app.graph.workflow import create_workflow

    workflow = create_workflow()

    result = await workflow.ainvoke({
        "query": query,
        "location": location,
        "days": days,
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
    })
    return result.get('final_response', '')


async def main():
    print("=" * 60)
    print("旅游规划助手 - 问答测试")
    print("输入 'q' 退出")
    print("=" * 60)

    test_questions = [
        ("北京明天天气怎么样？需要带伞吗？", "北京"),
        ("北京有什么好玩的景点推荐？", "北京"),
        ("上海市中心有什么性价比高的酒店？", "上海"),
        ("我想去成都玩3天，喜欢美食和自然风景", "成都"),
    ]

    for i, (question, location) in enumerate(test_questions, 1):
        print(f"\n{'─' * 60}")
        print(f"【问题{i}】{question}")
        print(f"{'─' * 60}")
        answer = await ask(question, location=location, days=3)
        print(f"【回答】\n{answer[:300]}...")

    print(f"\n{'=' * 60}")
    print("✅ 问答测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
