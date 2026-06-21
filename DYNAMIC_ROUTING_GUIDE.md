# 动态路由功能说明

## 概述

系统现已支持**智能动态路由**，能够根据用户需求自动判断需要运行哪些 Agent，避免不必要的 API 调用，提高响应速度和降低成本。

## 工作原理

### 之前的固定流程
```
用户请求 → 澄清节点 → 景点Agent → 天气Agent → 酒店Agent → 规划Agent → 输出
```
❌ **问题**: 无论用户需要什么，都执行所有 Agent，浪费资源

### 现在的动态路由
```
用户请求 → 路由节点(LLM决策) → 只运行需要的Agent → 规划Agent → 输出
```
✅ **优势**: 智能判断，按需执行

## 核心组件

### 1. Router Node（路由节点）

位于 [workflow.py](file:///D:/pythonProject4/实习项目/app/graph/workflow.py#L42-L110)，使用 LLM 分析用户需求并决定运行哪些 Agent。

**判断逻辑**:
- 提到"景点"、"玩"、"游览" → 包含 `attraction`
- 提到"天气"、"气候"、"下雨" → 包含 `weather`
- 提到"住宿"、"酒店"、"住哪里" → 包含 `hotel`
- 完整旅行规划（如"去X地玩N天"）→ 通常需要全部三个

**输出格式**:
```json
{
  "agents": ["attraction", "weather", "hotel"],
  "reason": "用户需要完整的3天旅行规划"
}
```

### 2. Dynamic Agent Node（动态 Agent 节点）

通用的 Agent 执行节点，可以执行任何类型的 Agent：
- `attraction`: 景点推荐
- `weather`: 天气查询
- `hotel`: 酒店推荐

### 3. 状态追踪

新增状态字段：
- `agents_to_run`: 需要运行的 Agent 列表
- `completed_agents`: 已完成的 Agent 列表
- `next_step`: 下一步执行的节点

## 使用示例

### 场景1: 完整旅行规划
```
用户: "我想去北京玩3天，喜欢历史文化和美食"
路由决策: ["attraction", "weather", "hotel"]
执行: 景点 + 天气 + 酒店 + 规划
```

### 场景2: 仅查询景点
```
用户: "北京有什么好玩的景点？"
路由决策: ["attraction"]
执行: 仅景点 Agent
```

### 场景3: 仅查询天气
```
用户: "北京明天天气怎么样？需要带伞吗？"
路由决策: ["weather"]
执行: 仅天气 Agent
```

### 场景4: 仅查询住宿
```
用户: "推荐几家北京市中心的酒店"
路由决策: ["hotel"]
执行: 仅酒店 Agent
```

### 场景5: 景点 + 天气
```
用户: "上海一日游攻略，需要了解天气"
路由决策: ["attraction", "weather"]
执行: 景点 + 天气 + 规划（跳过酒店）
```

## 测试方法

### 运行测试脚本
```bash
python test_dynamic_routing.py
```

这会测试5个不同场景，验证路由决策是否正确。

### 查看日志
启动服务后，日志会显示：
```
Executing router node - deciding which agents to run
Routing decision: ['attraction', 'weather'], Reason: 用户只需要景点和天气信息
Executing dynamic agent node: attraction
Completed attraction, next: weather
Executing dynamic agent node: weather
Completed weather, next: planner
```

## 优势对比

| 特性 | 固定流程 | 动态路由 |
|------|---------|---------|
| **API调用** | 总是调用所有API | 只调用需要的API |
| **响应速度** | 较慢（串行执行） | 更快（减少不必要调用） |
| **成本** | 高（每次都全量调用） | 低（按需调用） |
| **灵活性** | 低（固定流程） | 高（智能决策） |
| **用户体验** | 一般 | 更好（更快速） |

## 性能提升估算

假设各 Agent 平均耗时：
- Attraction: 2s (RAG检索 + API调用)
- Weather: 1s (API调用)
- Hotel: 2s (RAG检索 + API调用)

**场景对比**:

| 场景 | 固定流程耗时 | 动态路由耗时 | 节省时间 |
|------|------------|------------|---------|
| 仅查景点 | 5s | 2s | 60% ⚡ |
| 仅查天气 | 5s | 1s | 80% ⚡⚡ |
| 景点+天气 | 5s | 3s | 40% ⚡ |
| 完整规划 | 5s | 5s | 0% |

**平均节省**: 约 45% 的响应时间！

## 自定义路由规则

如果需要调整路由逻辑，修改 [router_node](file:///D:/pythonProject4/实习项目/app/graph/workflow.py#L42-L110) 中的系统提示：

```python
system_prompt = """
...
判断规则：
- 你的规则1
- 你的规则2
...
"""
```

## 添加新 Agent

如果要添加新的 Agent（如 `restaurant` 餐厅推荐）：

1. **创建 Agent**:
```python
async def restaurant_node(state: AgentState) -> AgentState:
    result = await restaurant_agent.execute({...})
    state['restaurant_result'] = result
    return state
```

2. **更新路由提示**:
```python
system_prompt = """
可用的 Agent 服务：
...
4. **restaurant** (餐厅推荐): 当用户询问美食、餐厅、吃饭等时使用
"""
```

3. **注册节点**:
```python
workflow.add_node("restaurant", restaurant_node)
```

4. **添加路由规则**:
```python
workflow.add_conditional_edges(
    "restaurant",
    route_after_agent,
    {
        "attraction": "attraction",
        "weather": "weather",
        "hotel": "hotel",
        "planner": "planner"
    }
)
```

## 容错机制

如果路由决策失败或出错：
1. **默认策略**: 运行所有 Agent（保证功能可用）
2. **Agent 执行失败**: 标记为完成，继续执行其他 Agent
3. **日志记录**: 详细记录错误信息便于调试

## 注意事项

1. **LLM 质量**: 路由准确性依赖 LLM 的理解能力
2. **提示词优化**: 可以根据实际使用情况优化路由提示
3. **监控日志**: 定期检查路由决策是否合理
4. **降级策略**: 确保即使路由失败也能正常工作

## 总结

动态路由功能让系统更加智能和高效：
- ✅ **智能决策**: LLM 理解用户需求，选择合适的 Agent
- ✅ **性能提升**: 减少不必要的 API 调用，响应更快
- ✅ **成本降低**: 按需调用，节省资源
- ✅ **灵活扩展**: 轻松添加新 Agent 和路由规则
- ✅ **稳定可靠**: 完善的容错和降级机制

这使得系统真正具备了智能 Agent 的能力！🎉
