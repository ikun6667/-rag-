
docker-compose up -d
第1步：安装Python依赖包
第2步：配置.env环境变量（包括千问模型的API地址和密钥）
第3步：启动MySQL和Redis基础服务 ← 当前问题所在
第4步：配置LLM服务（这里才涉及千问模型）
第5步：启动应用
# 快速启动指南

## 📦 第一步：安装依赖

```bash
pip install -r requirements.txt
```

## ⚙️ 第二步：配置环境

1. 复制环境配置文件：
```bash
cp .env .env
```

2. 编辑 `.env` 文件，配置您的参数：
   - 数据库连接信息
   - Redis 连接信息
   - 高德地图 API Key（可选）
   - LLM 服务地址（可选）

## 🗄️ 第三步：准备基础设施

### 选项 A：使用本地服务（推荐开发环境）

1. **启动 MySQL**
   ```bash
   # Windows (如果已安装 MySQL)
   net start MySQL80
   
   # 创建数据库
   mysql -u root -p
   CREATE DATABASE travel_planner;
   ```

2. **启动 Redis**
   ```bash
   # Windows (如果已安装 Redis)
   redis-server
   
   # 或使用 Docker
   docker run -d -p 6379:6379 redis
   ```

### 选项 B：使用 Docker（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: travel_planner
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

启动服务：
```bash
docker-compose up -d
```

## 🤖 第四步：配置 LLM（可选）

### 选项 A：使用 OpenAI API

修改 `.env`：
```env
LLM_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_key
```

### 选项 B：使用本地 vLLM（推荐）

1. 安装 vLLM：
```bash
pip install vllm
```

2. 启动 vLLM 服务：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --port 8001 \
    --tensor-parallel-size 1
```

> 注意：需要足够的 GPU 显存（建议 16GB+）

### 选项 C：使用其他兼容 OpenAI API 的服务

修改 `.env` 中的 `LLM_API_BASE` 和 `LLM_MODEL_NAME`

## 🚀 第五步：启动应用

```bash
python main.py
```

或：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动

## ✅ 第六步：验证安装

1. **访问健康检查端点**：
```bash
curl http://localhost:8000/health
```

应返回：
```json
{
  "status": "ok",
  "timestamp": 1234567890.123
}
```

2. **访问 API 文档**：
在浏览器中打开：`http://localhost:8000/docs`

3. **运行测试脚本**：
```bash
python test_api.py
```

## 📊 第七步：处理知识库数据（可选）

1. 准备旅游知识文本文件，放入 `data/knowledge_base/` 目录

2. 调用数据处理 API：
```bash
curl -X POST "http://localhost:8000/api/data/process" \
  -H "Content-Type: application/json" \
  -d '{
    "data_dir": "./data/knowledge_base",
    "rebuild_index": true
  }'
```

## 🎯 第八步：测试旅行规划

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

## 🔧 常见问题

### 1. 无法连接 MySQL
```
错误：Can't connect to MySQL server
```
解决：
- 检查 MySQL 服务是否启动
- 确认 `.env` 中的连接信息正确
- 测试连接：`mysql -h localhost -u root -p`

### 2. 无法连接 Redis
```
错误：Error connecting to Redis
```
解决：
- 检查 Redis 服务是否启动
- 测试连接：`redis-cli ping`（应返回 PONG）

### 3. LLM 服务不可用
```
错误：Connection refused to LLM API
```
解决：
- 检查 vLLM 或其他 LLM 服务是否启动
- 确认 `LLM_API_BASE` 地址正确
- 查看 LLM 服务日志

### 4. 高德地图 API 失败
```
警告：AMap API error
```
解决：
- 检查 `AMAP_API_KEY` 是否配置
- 确认 API Key 有效且有配额
- 如不使用，可忽略此警告（系统会降级运行）

### 5. 内存不足
```
错误：CUDA out of memory
```
解决：
- 减小模型大小或使用量化版本
- 降低 `LLM_MAX_TOKENS`
- 使用 CPU 推理（较慢）

## 📝 下一步

1. **查看 API 文档**：`http://localhost:8000/docs`
2. **阅读完整文档**：查看 README.md
3. **自定义配置**：修改 `app/core/config.py`
4. **添加新功能**：参考开发指南

## 💡 提示

- 开发时启用 `DEBUG=True` 查看详细日志
- 生产环境请修改默认密码和密钥
- 定期清理 ChromaDB 和 Redis 缓存
- 监控 GPU 使用情况（如果使用本地模型）

## 🆘 获取帮助

如遇到问题：
1. 查看控制台日志
2. 检查 `.env` 配置
3. 确认所有依赖服务正常运行
4. 查阅 README.md 和本文档
5. 提交 Issue

祝您使用愉快！🎉
