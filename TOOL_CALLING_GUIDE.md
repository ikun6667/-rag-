# MCP 工具调用功能说明

## 概述

本项目现已支持**动态工具调用**功能，LLM可以根据用户需求自主决定调用哪些工具、何时调用以及如何传参。

## 架构改进

### 之前（硬编码调用）
```python
# Agent 中直接调用服务
attractions = await amap_service.search_poi(
    keywords=query,
    city=location,
    types="旅游景点"
)
```

### 现在（动态工具调用）
```python
# LLM 自主决定调用工具
messages = [system_message, human_message]
result = await self._call_llm_with_tools(messages, max_iterations=2)
# LLM 输出: {"name": "search_poi", "args": {"keywords": "故宫", "city": "北京", "types": "旅游景点"}}
```

## 核心组件

### 1. 工具定义 (`app/mcp/tools.py`)

将高德地图服务封装为 LangChain Tools：

- **search_poi**: 搜索兴趣点（景点、酒店、餐厅等）
- **get_weather**: 查询城市天气
- **calculate_route**: 路线规划
- **get_place_details**: 获取地点详情

每个工具都有详细的描述，帮助 LLM 理解何时如何使用。

### 2. BaseAgent 增强 (`app/agents/base_agent.py`)

新增方法：
- `_call_llm_with_tools()`: 支持多轮工具调用的LLM交互
- `_execute_tool()`: 执行单个工具并返回结果

工作流程：
```
LLM → 决定是否调用工具 
  ↓ (需要调用)
解析工具名称和参数 → 执行工具 → 返回结果给LLM
  ↓
LLM → 基于工具结果生成最终回复
```

### 3. Agent 更新

所有 Agent 都已更新为使用工具调用：

#### AttractionAgent
```python
tools = [amap_tools[0]]  # search_poi tool
```

#### WeatherAgent
```python
tools = [amap_tools[1]]  # get_weather tool
```

#### HotelAgent
```python
tools = [amap_tools[0]]  # search_poi tool (用于搜索酒店)
```

## 使用示例

### 方式1: 通过 API 测试

启动服务器后：
```bash
python main.py
```

发送请求：
```bash
curl -X POST http://localhost:8000/api/travel/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我想去北京玩3天",
    "location": "北京",
    "days": 3,
    "budget": "中等",
    "preferences": "喜欢历史文化和美食"
  }'
```

### 方式2: 直接测试工具调用

```bash
python test_tool_calling.py
```

这会测试各个 Agent 的工具调用功能。

### 方式3: 在代码中使用

```python
from app.agents.attraction_agent import attraction_agent

result = await attraction_agent.execute({
    'query': '故宫',
    'location': '北京',
    'preferences': '历史文化',
    'budget': '中等'
})

print(result['recommendation'])
print(result['attractions'])
```

## 优势对比

| 特性 | 旧方案（硬编码） | 新方案（工具调用） |
|------|-----------------|-------------------|
| **灵活性** | 固定流程 | LLM动态决策 |
| **扩展性** | 需修改代码 | 只需注册新工具 |
| **智能性** | 被动执行 | 主动选择工具 |
| **组合能力** | 单一调用 | 多工具组合使用 |
| **容错性** | 出错即失败 | 可回退到直接调用 |

## 工作原理

### 1. 工具注册
```python
@tool
async def search_poi(keywords: str, city: str = "全国", types: str = "旅游景点") -> str:
    """搜索兴趣点..."""
    ...
```

### 2. Agent 初始化时绑定工具
```python
self.llm_with_tools = self.llm.chat_model.bind_tools(self.tools)
```

### 3. 多轮工具调用循环
```python
for iteration in range(max_iterations):
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        # 执行工具
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)
            messages.append(ToolMessage(result))
    else:
        # 返回最终回复
        return response.content
```

## 降级策略

如果工具调用失败，系统会自动回退到直接调用方式：

```python
try:
    # 尝试工具调用
    result = await self._call_llm_with_tools(messages)
except Exception as e:
    # 回退到直接调用
    logger.warning("Tool calling failed, falling back to direct call")
    result = await amap_service.search_poi(...)
```

这确保了系统的稳定性。

## 添加新工具

1. 在 `app/mcp/tools.py` 中定义新工具：
```python
@tool
async def my_new_tool(param1: str, param2: int) -> str:
    """工具描述..."""
    result = await some_service.do_something(param1, param2)
    return json.dumps(result, ensure_ascii=False)
```

2. 添加到工具列表：
```python
amap_tools = [
    search_poi,
    get_weather,
    calculate_route,
    get_place_details,
    my_new_tool  # 新增
]
```

3. 在 Agent 中使用：
```python
tools = [amap_tools[-1]]  # 使用新工具
super().__init__(name="my_agent", tools=tools)
```

## 注意事项

1. **LLM 支持**: 确保使用的 LLM 模型支持 function calling（Qwen2.5 支持）
2. **异步工具**: 所有工具都是异步的，需要使用 `await`
3. **JSON 格式**: 工具返回必须是 JSON 字符串格式
4. **错误处理**: 工具内部应捕获异常并返回错误信息
5. **迭代限制**: 默认最大3次工具调用迭代，避免无限循环

## 调试技巧

查看日志了解工具调用过程：
```bash
# 设置日志级别
export LOG_LEVEL=INFO
python main.py
```

日志会显示：
- LLM 决定调用哪些工具
- 工具执行的参数
- 工具返回的结果
- 是否触发降级策略

## 总结

现在系统具备了真正的 Agent 能力：
- ✅ **自主决策**: LLM 根据上下文决定调用什么工具
- ✅ **动态参数**: 参数由 LLM 生成，不是硬编码
- ✅ **多轮交互**: 可以连续调用多个工具
- ✅ **灵活扩展**: 轻松添加新工具
- ✅ **稳定可靠**: 有完善的降级机制

这使得系统更加智能和灵活！🎉
