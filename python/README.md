# Python 服务端骨架

这个 FastAPI 工程已经按”先做聊天，再升级 Agent”的思路分层，后续扩展时不需要重搭结构。

当前分层：

- `app/api/`：接口路由层（chat、conversations、health）
- `app/schemas/`：请求和响应模型
- `app/services/llm.py`：DeepSeek 兼容聊天调用与流式输出入口
- `app/services/agent.py`：后续 Agent 编排入口
- `app/services/conversation.py`：会话 CRUD、上一轮删除、消息持久化
- `app/core/config.py`：环境变量和基础配置
- `app/core/database.py`：SQLite 数据库连接管理与建表

运行配置说明：

1. 真实运行配置放在 `python/.env`
2. `python/.env.example` 只是模板文件，不参与真实运行
3. 修改配置项时，需要同时同步 `.env.example` 模板和相关 README
4. 当前本地开发建议使用 `uvicorn app.main:app --reload --port 8001`，避免和残留的 `8000` 进程冲突
5. 数据库文件会固定创建在 `python/agent_demo.db`，已加入 `.gitignore`

后续演进建议：

1. 当前普通对话和 SSE 流式对话都已经接通真实 DeepSeek 调用。
2. 会话历史已通过 SQLite 持久化，支持多会话管理、上一轮重试前清理，以及停止生成后的 partial reply 保留。
3. 新会话改为首条用户消息到达时懒创建，不再因为点击“新对话”产生空记录。
4. 等需要工具调用时，再把调度逻辑逐步放进 `AgentService`。

文档维护约定：

1. `python/` 及其主要子目录都带有 `README.md`。
2. 只要目录职责、配置方式、接口协议或服务分层发生变化，必须同步更新对应目录的说明文档。
