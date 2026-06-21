"""
查看 Redis 缓存内容
"""
import os
# 禁用 ChromaDB 遥测
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from app.core.database import redis_client
import json

def view_redis_cache():
    print("="*80)
    print("Redis 缓存内容查看")
    print("="*80)
    
    # 获取所有键
    all_keys = redis_client.keys("*")
    
    if not all_keys:
        print("\n⚠️  缓存为空，还没有任何数据")
        return
    
    print(f"\n📊 总缓存键数量: {len(all_keys)}\n")
    
    # 按类型分组统计
    type_stats = {}
    for key in all_keys:
        prefix = key.split(":")[0]
        type_stats[prefix] = type_stats.get(prefix, 0) + 1
    
    print("📈 缓存类型分布:")
    for cache_type, count in sorted(type_stats.items()):
        print(f"  - {cache_type}: {count} 个")
    
    print("\n" + "="*80)
    print("详细缓存内容:")
    print("="*80)
    
    # 显示每个键的详细信息
    for i, key in enumerate(sorted(all_keys), 1):
        print(f"\n[{i}] 键: {key}")
        
        # 获取值
        value = redis_client.get(key)
        if value:
            try:
                # 尝试解析 JSON
                parsed = json.loads(value)
                if isinstance(parsed, (dict, list)):
                    print(f"    值: {json.dumps(parsed, ensure_ascii=False, indent=4)[:500]}...")
                else:
                    print(f"    值: {str(parsed)[:200]}")
            except:
                print(f"    值: {value[:200]}")
        
        # 获取 TTL
        ttl = redis_client.ttl(key)
        if ttl > 0:
            print(f"    过期时间: {ttl} 秒")
        else:
            print(f"    过期时间: 永久")

if __name__ == "__main__":
    view_redis_cache()
