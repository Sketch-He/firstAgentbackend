# Python 服务端骨架

这个 FastAPI 工程已经按“先做聊天，再升级 Agent”的思路分层，后续扩展时不需要重搭结构。

当前分层：

- `app/api/`：接口路由层
- `app/schemas/`：请求和响应模型
- `app/services/llm.py`：DeepSeek 兼容聊天调用与流式输出入口
- `app/services/agent.py`：后续 Agent 编排入口
- `app/core/config.py`：环境变量和基础配置

运行配置说明：

1. 真实运行配置放在 `python/.env`
2. `python/.env.example` 只是模板文件，不参与真实运行
3. 修改配置项时，需要同时同步 `.env.example` 模板和相关 README
4. 当前本地开发建议使用 `uvicorn app.main:app --reload --port 8001`，避免和残留的 `8000` 进程冲突

后续演进建议：

1. 当前普通对话和 SSE 流式对话都已经接通真实 DeepSeek 调用。
2. 下一步优先完善前端流式体验，例如自动滚动、停止生成、重试。
3. 等需要工具调用时，再把调度逻辑逐步放进 `AgentService`。

文档维护约定：

1. `python/` 及其主要子目录都带有 `README.md`。
2. 只要目录职责、配置方式、接口协议或服务分层发生变化，必须同步更新对应目录的说明文档。
