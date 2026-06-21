# RAG 和 MCP 工具评估指南

## 📋 概述

本项目包含三个评估工具：
1. **RAG 召回率评估**：测试检索系统的相关性和召回质量
2. **MCP 单一工具调用成功率评估**：直接测试每个工具的调用成功率和性能
3. **端到端工具选择成功率评估**：基于 Workflow 的自然语言交互测试，验证系统能否正确理解用户需求并选择合适的 Agent

## 📁 文件结构

```
data/knowledge/              # RAG 知识库数据目录
├── beijing_forbidden_city.txt    # 北京故宫旅游攻略
├── shanghai_bund.txt             # 上海外滩旅游攻略
├── chengdu_kuanzhai.txt          # 成都宽窄巷子旅游攻略
├── hangzhou_westlake.txt         # 杭州西湖旅游攻略
└── xian_terraccotta.txt          # 西安兵马俑旅游攻略

app/rag/evaluation.py        # RAG 召回率评估工具
app/mcp/evaluation.py        # MCP 单一工具调用评估工具
app/mcp/e2e_evaluation.py    # 端到端工具选择评估工具（Workflow）
test_evaluation.py           # 综合评估测试脚本
```

## 🚀 快速开始

### 1. 运行综合评估测试

```bash
python test_evaluation.py
```

这将依次执行：
- RAG 数据处理和索引构建
- RAG 召回率评估（10个测试查询）
- MCP 单一工具调用成功率评估（12个测试用例）
- 端到端工具选择成功率评估（15个自然语言场景）
- 生成评估报告

### 2. 单独运行 RAG 召回率评估

```python
from app.rag.data_processor import data_processor
from app.rag.evaluation import recall_evaluator

# 处理知识库数据
stats = data_processor.process_pipeline("data/knowledge", rebuild_index=True)

# 加载测试集并评估
recall_evaluator.load_test_dataset()
results = recall_evaluator.evaluate(top_k=5)

# 保存结果
recall_evaluator.save_results(results, "rag_evaluation_results.json")
```

### 3. 单独运行工具调用成功率评估

```python
import asyncio
from app.mcp.evaluation import tool_evaluator

async def main():
    # 加载测试用例
    tool_evaluator.load_test_cases()
    
    # 执行评估
    results = await tool_evaluator.evaluate_all()
    
    # 保存结果
    tool_evaluator.save_results(results, "tool_evaluation_results.json")

asyncio.run(main())
```

### 3. 单独运行端到端工具选择评估

```python
import asyncio
from app.mcp.e2e_evaluation import e2e_evaluator

async def main():
    # 加载测试用例（15个真实场景）
    e2e_evaluator.load_test_cases()
    
    # 执行评估
    results = await e2e_evaluator.evaluate_all()
    
    # 保存结果
    e2e_evaluator.save_results(results, "e2e_tool_evaluation_results.json")

asyncio.run(main())
```

**这个测试的特点：**
- ✅ 模拟真实用户自然语言交互
- ✅ 测试智能路由决策能力
- ✅ 验证 Agent 选择是否正确
- ✅ 检查完整的工作流是否正常运行
- ✅ 覆盖多种场景类型（纯天气、纯景点、纯酒店、组合查询等）

## 📊 评估指标说明

### RAG 召回率评估指标

1. **Recall@K (召回率)**
   - 衡量相关文档被检索到的比例
   - 值域：0-1，越高越好

2. **Precision@K (精确率)**
   - 衡量检索结果中相关文档的比例
   - 值域：0-1，越高越好

3. **MRR (Mean Reciprocal Rank)**
   - 平均倒数排名，衡量第一个相关文档的排名
   - 值域：0-1，越高越好

### MCP 单一工具调用评估指标

1. **成功率 (Success Rate)**
   - 成功调用的工具占总调用的比例
   - 计算公式：成功次数 / 总次数 × 100%

2. **平均响应时间 (Average Response Time)**
   - 工具调用的平均耗时（秒）
   - 越低越好

3. **各工具详细统计**
   - 每个工具的调用次数、成功率、平均响应时间

### 端到端工具选择评估指标（Workflow 自然语言交互）

1. **总体成功率 (Overall Success Rate)**
   - Agent 选择正确且路由正确的测试用例比例
   - 反映系统整体表现

2. **Agent 选择准确率 (Agent Selection Accuracy)**
   - 系统选择的 Agent 是否包含用户期望的所有 Agent
   - 衡量智能路由的准确性

3. **路由正确率 (Routing Accuracy)**
   - 工作流是否正确执行并返回合理长度的响应
   - 验证整个流程是否正常

4. **场景类型统计**
   - 按预期 Agent 组合分组统计（如纯 weather、weather+attraction 等）
   - 识别哪些场景类型更容易出错

## 📝 自定义测试数据

### 自定义 RAG 测试集

创建 JSON 文件 `custom_rag_test.json`：

```json
{
  "queries": [
    "你的测试查询1",
    "你的测试查询2"
  ],
  "ground_truth": [
    {
      "query": "你的测试查询1",
      "relevant_docs": [0, 1]
    },
    {
      "query": "你的测试查询2",
      "relevant_docs": [2]
    }
  ]
}
```

然后加载：
```python
recall_evaluator.load_test_dataset("custom_rag_test.json")
```

### 自定义工具调用测试集

创建 JSON 文件 `custom_tool_test.json`：

```json
{
  "test_cases": [
    {
      "tool": "search_poi",
      "params": {"keywords": "景点", "city": "城市名", "types": "旅游景点"},
      "description": "测试描述"
    },
    {
      "tool": "get_weather",
      "params": {"city": "城市名"},
      "description": "测试描述"
    }
  ]
}
```

然后加载：
```python
tool_evaluator.load_test_cases("custom_tool_test.json")
```

## 📈 输出结果

评估完成后会生成三个 JSON 文件：

1. **rag_evaluation_results.json**
   ```json
   {
     "avg_recall": 0.85,
     "avg_precision": 0.72,
     "mrr": 0.90,
     "num_queries": 10,
     "detailed_results": [...]
   }
   ```

2. **tool_evaluation_results.json**（单一工具测试）
   ```json
   {
     "total_tests": 12,
     "success_count": 12,
     "failed_count": 0,
     "success_rate": 100.0,
     "avg_response_time": 1.25,
     "tool_statistics": {...},
     "detailed_results": [...]
   }
   ```

3. **e2e_tool_evaluation_results.json**（端到端测试）
   ```json
   {
     "total_tests": 15,
     "success_count": 13,
     "failed_count": 2,
     "success_rate": 86.67,
     "agent_selection_accuracy": 93.33,
     "routing_accuracy": 93.33,
     "avg_response_time": 5.80,
     "scenario_statistics": {
       "weather": {"total": 3, "success": 3, ...},
       "attraction": {"total": 2, "success": 2, ...},
       "attraction,weather": {"total": 4, "success": 3, ...}
     },
     "detailed_results": [...]
   }
   ```

## 🔧 故障排查

### 问题 1: RAG 召回率低

**可能原因：**
- 知识库数据不足
- 查询与文档关键词不匹配
- 分块大小不合适

**解决方案：**
- 增加更多高质量的知识库文档
- 优化文档内容和关键词
- 调整 `chunk_size` 参数（默认 500）

### 问题 2: 工具调用失败

**可能原因：**
- 高德地图 API Key 未配置或无效
- 网络连接问题
- API 调用频率限制

**解决方案：**
- 检查 `.env` 文件中的 `AMAP_API_KEY` 配置
- 确保网络连接正常
- 降低测试频率或联系高德地图提升配额

### 问题 3: 评估脚本报错

**可能原因：**
- 依赖包未安装
- 知识库目录不存在
- Redis 缓存问题

**解决方案：**
```bash
# 安装依赖
pip install -r requirements.txt

# 创建知识库目录
mkdir -p data/knowledge

# 清空 Redis 缓存
redis-cli FLUSHDB
```

## 💡 最佳实践

1. **定期评估**：建议在每次更新知识库或修改检索算法后重新评估

2. **多样化测试集**：使用不同类型的查询来全面评估系统性能

3. **监控趋势**：保存历史评估结果，观察性能变化趋势

4. **优化迭代**：根据评估结果针对性地优化系统：
   - 召回率低 → 改进检索算法或增加数据
   - 精确率低 → 优化排序或重排策略
   - 工具成功率低 → 检查 API 配置和网络

5. **结合实际场景**：根据实际用户查询模式设计测试用例

## 📚 相关文档

- [RAG 检索评分机制](../README.md#rag-检索评分机制)
- [MCP 工具调用指南](../TOOL_CALLING_GUIDE.md)
- [动态路由机制](../DYNAMIC_ROUTING_GUIDE.md)

## 🤝 贡献

欢迎提交新的测试用例或改进评估方法！
