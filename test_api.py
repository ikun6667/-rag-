"""
简单测试脚本 - 验证系统功能
"""
import requests
import json


def test_health():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_travel_plan():
    """测试旅行规划"""
    print("=== 测试旅行规划 ===")
    data = {
        "query": "我想去北京玩3天",
        "location": "北京",
        "days": 3,
        "budget": "中等",
        "preferences": "喜欢历史文化和美食"
    }
    
    response = requests.post(
        "http://localhost:8000/api/travel/plan",
        json=data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('data'):
            itinerary = result['data'].get('itinerary', '')
            print(f"\n行程规划:\n{itinerary[:500]}...")
    else:
        print(f"Error: {response.text}")
    print()


def test_rag_search():
    """测试 RAG 搜索"""
    print("=== 测试 RAG 搜索 ===")
    response = requests.get(
        "http://localhost:8000/api/rag/search",
        params={"query": "北京故宫", "top_k": 3}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('data'):
            print(f"找到 {len(result['data'])} 条结果")
            for i, item in enumerate(result['data'][:2], 1):
                print(f"\n结果 {i}:")
                print(f"  文档: {item.get('document', '')[:100]}...")
                print(f"  分数: {item.get('rerank_score', item.get('score', 'N/A'))}")
    else:
        print(f"Error: {response.text}")
    print()


def test_stats():
    """测试统计信息"""
    print("=== 测试统计信息 ===")
    response = requests.get("http://localhost:8000/api/stats")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")
    print()


if __name__ == "__main__":
    print("开始测试多 Agent 旅游规划系统...\n")
    
    try:
        # 运行测试
        test_health()
        test_stats()
        test_rag_search()
        test_travel_plan()
        
        print("\n✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到服务器")
        print("请确保服务已启动：python main.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
