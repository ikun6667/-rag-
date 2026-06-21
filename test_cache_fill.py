"""
测试 Agent 缓存功能
"""
import asyncio
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from app.agents.weather_agent import weather_agent
from app.agents.attraction_agent import attraction_agent
from view_redis import view_redis_cache

async def test_cache():
    print("="*80)
    print("测试 Agent 缓存功能")
    print("="*80)
    
    # 测试1：天气 Agent
    print("\n[测试 1] 查询北京天气...")
    try:
        result = await weather_agent.execute({
            'location': '北京',
            'date': '2024-01-01'
        })
        print(f"✓ 天气查询成功")
        print(f"  建议长度: {len(result.get('suggestion', ''))} 字符")
    except Exception as e:
        print(f"✗ 天气查询失败: {e}")
    
    # 测试2：景点 Agent
    print("\n[测试 2] 查询北京景点...")
    try:
        result = await attraction_agent.execute({
            'location': '北京',
            'preferences': '历史文化'
        })
        print(f"✓ 景点查询成功")
        print(f"  推荐数量: {len(result.get('attractions', []))}")
    except Exception as e:
        print(f"✗ 景点查询失败: {e}")
    
    # 查看缓存
    print("\n" + "="*80)
    print("查看 Redis 缓存...")
    print("="*80)
    view_redis_cache()

if __name__ == "__main__":
    asyncio.run(test_cache())
