"""
测试工具调用功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_tool_calling():
    """测试工具调用功能"""
    print("=" * 60)
    print("测试 MCP 工具调用功能")
    print("=" * 60)
    
    # 测试1: 景点推荐 Agent
    print("\n【测试1】景点推荐 Agent - 使用工具调用")
    print("-" * 60)
    from app.agents.attraction_agent import attraction_agent
    
    result = await attraction_agent.execute({
        'query': '故宫',
        'location': '北京',
        'preferences': '历史文化',
        'budget': '中等'
    })
    
    print(f"状态: {result['status']}")
    print(f"推荐数量: {len(result.get('attractions', []))}")
    if result.get('attractions'):
        print(f"第一个景点: {result['attractions'][0].get('name', 'N/A')}")
    print(f"推荐理由预览: {result.get('recommendation', '')[:100]}...")
    
    # 测试2: 天气查询 Agent
    print("\n【测试2】天气查询 Agent - 使用工具调用")
    print("-" * 60)
    from app.agents.weather_agent import weather_agent
    
    result = await weather_agent.execute({
        'location': '北京',
        'date': '2026-06-07'
    })
    
    print(f"状态: {result['status']}")
    print(f"天气数据: {result.get('weather', {})}")
    print(f"出行建议预览: {result.get('suggestion', '')[:100]}...")
    
    # 测试3: 酒店推荐 Agent
    print("\n【测试3】酒店推荐 Agent - 使用工具调用")
    print("-" * 60)
    from app.agents.hotel_agent import hotel_agent
    
    result = await hotel_agent.execute({
        'location': '北京',
        'check_in': '2026-06-08',
        'check_out': '2026-06-10',
        'budget': '中等',
        'preferences': '靠近市中心'
    })
    
    print(f"状态: {result['status']}")
    print(f"酒店数量: {len(result.get('hotels', []))}")
    if result.get('hotels'):
        print(f"第一个酒店: {result['hotels'][0].get('name', 'N/A')}")
    print(f"推荐理由预览: {result.get('recommendation', '')[:100]}...")
    
    # 测试4: 直接测试工具定义
    print("\n【测试4】直接测试工具定义")
    print("-" * 60)
    from app.mcp.tools import amap_tools, TOOLS_DESCRIPTION
    
    print(f"已定义工具数量: {len(amap_tools)}")
    for tool in amap_tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    
    print(f"\n工具描述:\n{TOOLS_DESCRIPTION}")
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_tool_calling())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
