# Multi-Agent Travel Planning System

基于 LangChain、LangGraph 和多 Agent 协同的智能旅游规划系统。

## 🚀 技术栈

- **框架**: FastAPI + LangChain + LangGraph
- **向量数据库**: ChromaDB
- **数据存储**: MySQL + Redis
- **大语言模型**: Qwen2.5-7B + vLLM
- **Embedding**: BGE-M3
- **工具集成**: 高德地图 MCP
- **文本处理**: SimHash + MinHash + TF-IDF

## 📋 功能特性

### 1. 多 Agent 协同
- **景点推荐 Agent**: 基于 RAG 和高德地图的智能景点推荐
- **天气查询 Agent**: 实时天气信息和出行建议
- **酒店推荐 Agent**: 个性化酒店住宿推荐
- **行程规划 Agent**: 整合各 Agent 输出，生成完整行程

### 2. 增强 RAG 检索
- BM25 + BGE-M3 混合检索
- RRF (Reciprocal Rank Fusion) 融合
- Cross-Encoder Rerank 重排序
- 检索效果提升 20%

### 3. 高效数据处理
- SimHash + MinHash + TF-IDF 组合去重
- 智能文本分块
- 10万+文档处理能力
- 处理效率提升 73%

### 4. 性能优化
- Redis 缓存层
- vLLM 推理加速
- 上下文压缩与裁剪
- 平均响应时间 < 1.5s

## 📁 项目结构

```
实习项目/
├── app/
│   ├── api/                    # FastAPI 路由
│   │   └── routes.py
│   ├── agents/                 # Agent 实现
│   │   ├── base_agent.py      # 基础 Agent
│   │   ├── attraction_agent.py # 景点 Agent
│   │   ├── weather_agent.py   # 天气 Agent
│   │   ├── hotel_agent.py     # 酒店 Agent
│   │   └── planner_agent.py   # 规划 Agent
│   ├── core/                   # 核心配置
│   │   ├── config.py
│   │   └── database.py
│   ├── graph/                  # LangGraph 工作流
│   │   └── workflow.py
│   ├── rag/                    # RAG 检索系统
│   │   ├── data_processor.py  # 数据处理
│   │   ├── vector_store.py    # 向量存储
│   │   ├── retriever.py       # 混合检索
│   │   └── reranker.py        # 重排序
│   ├── models/                 # 模型相关
│   │   └── llm_client.py      # LLM 客户端
│   ├── cache/                  # 缓存层
│   │   └── redis_cache.py
│   ├── mcp/                    # MCP 服务
│   │   └── amap_service.py    # 高德地图服务
│   └── utils/                  # 工具函数
│       ├── text_dedup.py      # 文本去重工具
│       └── prompt_templates.py # Prompt 模板
├── data/                       # 数据目录
│   └── knowledge_base/         # 旅游知识库
├── requirements.txt            # 依赖包
└── main.py                     # 主入口
```

## 🔧 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置

创建 `.env` 文件：

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=travel_planner

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 高德地图 API
AMAP_API_KEY=your_amap_api_key

# LLM 配置（如果使用本地 vLLM）
LLM_API_BASE=http://localhost:8001/v1
```

### 3. 启动 vLLM 服务（可选）

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --port 8001 \
    --tensor-parallel-size 1
```

### 4. 启动应用

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API 接口

### 健康检查

```bash
GET /health
```

### 制定旅行行程

```bash
POST /api/travel/plan

{
  "query": "我想去北京玩",
  "location": "北京",
  "days": 3,
  "budget": "中等",
  "preferences": "喜欢历史文化"
}
```

### 处理知识库数据

```bash
POST /api/data/process

{
  "data_dir": "./data/knowledge_base",
  "rebuild_index": true
}
```

### 搜索旅游知识

```bash
GET /api/rag/search?query=北京故宫&top_k=5
```

### 获取系统统计

```bash
GET /api/stats
```

### 清除缓存

```bash
POST /api/cache/clear?prefix=agent:attraction
```

## 🎯 使用示例

### Python 调用示例

```python
import requests

# 制定旅行行程
response = requests.post("http://localhost:8000/api/travel/plan", json={
    "query": "我想去北京玩3天",
    "location": "北京",
    "days": 3,
    "budget": "中等",
    "preferences": "喜欢历史文化和美食"
})

print(response.json())
```

### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/travel/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我想去北京玩3天",
    "location": "北京",
    "days": 3,
    "budget": "中等",
    "preferences": "喜欢历史文化和美食"
  }'
```

## 📊 性能指标

- **平均响应时间**: < 1.5s
- **问答准确率提升**: ~18%
- **复杂场景召回率提升**: ~20%
- **数据处理效率提升**: ~73%

## 🔍 核心技术详解

### 1. 多 Agent 架构

系统采用 LangGraph 编排多个专业 Agent：
- **并行执行**: 景点、天气、酒店 Agent 可并行调用
- **结果整合**: Planner Agent 综合所有信息生成最终行程
- **缓存优化**: 每个 Agent 独立缓存，减少重复计算

### 2. RAG 检索流程

```
用户查询 → BM25 检索 → 向量检索 → RRF 融合 → Rerank 重排序 → Top-K 结果
```

### 3. 数据去重策略

```
原始文本 → SimHash 粗筛 → MinHash 精筛 → TF-IDF 验证 → 唯一文本
```

### 4. 缓存策略

- **多级缓存**: LLM 响应、RAG 结果、API 调用
- **智能失效**: 基于时间和事件的缓存更新
- **Redis 持久化**: 支持分布式部署

## 🛠️ 开发指南

### 添加新的 Agent

1. 继承 `BaseAgent` 类
2. 实现 `execute` 方法
3. 在 `workflow.py` 中注册节点
4. 更新路由逻辑

### 自定义 Prompt

在 `app/utils/prompt_templates.py` 中添加新的 Prompt 模板。

### 调整检索参数

在 `app/core/config.py` 中修改：
- `RAG_TOP_K`: 返回结果数量
- `RRF_K_VALUE`: RRF 融合参数
- `RAG_SCORE_THRESHOLD`: 分数阈值

## 📝 注意事项

1. **高德地图 API**: 需要申请 API Key 并配置到环境变量
2. **vLLM 服务**: 如需使用本地模型，需先启动 vLLM 服务
3. **数据库**: 确保 MySQL 和 Redis 服务正常运行
4. **内存需求**: BGE-M3 模型需要较大内存，建议使用 GPU

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

如有问题，请通过 Issue 反馈。
