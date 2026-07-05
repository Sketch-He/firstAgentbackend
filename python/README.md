# python 服务端骨架

这个 FastAPI 工程已经按“先做聊天，再升级 Agent”的思路分层，当前推荐部署目标是 `Railway`。

## 当前分层

- `app/api/`：接口路由层（chat、conversations、health、documents）
- `app/schemas/`：请求和响应模型
- `app/services/llm.py`：DeepSeek 兼容聊天调用与流式输出入口
- `app/services/agent.py`：后续 Agent 编排入口
- `app/services/conversation.py`：会话 CRUD、上一轮删除、消息持久化
- `app/services/document.py`：文档解析、分块、文档记录 CRUD
- `app/services/vector_store.py`：ChromaDB 向量存储与检索
- `app/services/rag.py`：RAG 检索增强生成服务
- `app/core/config.py`：环境变量和基础配置
- `app/core/database.py`：SQLite 数据库连接管理与建表

## 当前部署状态

1. 服务端已经补齐 `Dockerfile`，可作为 Railway Web Service 直接部署。
2. 已新增 `python/.dockerignore`，避免把 `.env`、数据库文件和虚拟环境打进镜像。
3. SQLite 路径已由固定文件改成 `SQLITE_PATH` 环境变量控制。
4. 相对路径会自动落到 `python/` 目录下，绝对路径可直接用于 Railway volume。
5. 当前建议的 Railway volume 数据文件路径是 `/data/agent_demo.db`。

## 现在要做什么

1. 在 Railway 从 GitHub 导入仓库。
2. 把服务根目录设置为 `python/`。
3. 给服务挂一个 volume，挂载路径建议为 `/data`。
4. 在 Railway 配置以下环境变量：

```bash
APP_NAME=Agent Demo API
API_PREFIX=/api
CORS_ORIGINS_RAW=https://<your-frontend-domain>
SQLITE_PATH=/data/agent_demo.db
OPENAI_API_KEY=<your-deepseek-key>
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
ASSISTANT_SYSTEM_PROMPT=你是一个中文 AI 助手，请优先给出准确、直接、可执行的回答。
REQUEST_TIMEOUT_SECONDS=60
```

5. 部署后先验证：
   `GET /health`
   `GET /`
   `POST /api/chat/stream`

## 接下来要做什么

1. 把 SQLite 替换成 `Postgres`。
2. 把 CORS 从单一生产域名扩展成正式环境与预览环境的清单。
3. 增加结构化日志、错误追踪和最小的速率限制。
4. 为后续 Agent 能力预留更清晰的工具调用与持久化抽象。

## 运行配置说明

1. 真实运行配置放在 `python/.env`。
2. `python/.env.example` 只作为模板文件，不参与真实运行。
3. 修改配置项时，需要同时同步 `.env.example` 模板和相关 README。
4. 当前本地开发建议使用 `uvicorn app.main:app --reload --port 8001`，避免和残留的 `8000` 进程冲突。

## 本地运行

```bash
cd python
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8001
```

## 本地 Docker 验证

```bash
cd python
docker build -t agent-demo-api .
docker run --rm -p 8001:8001 --env-file .env agent-demo-api
```

## 文档维护约定

1. `python/` 及其主要子目录都带有 `README.md`。
2. 只要目录职责、配置方式、接口协议或服务分层发生变化，必须同步更新对应目录的说明文档。
