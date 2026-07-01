# Agent Demo 项目骨架

当前工作区拆成两个实现目录：

- `frontend/`：基于 `Vue 3 + Vite + TypeScript` 的前端聊天页面
- `python/`：基于 `FastAPI` 的 Python 服务端

## 当前范围

- 一个可继续扩展的聊天产品外壳
- 前端消息列表、输入区、会话侧栏和基础 Markdown 渲染
- 后端真实 DeepSeek 兼容聊天服务与 SSE 流式输出
- 对话历史持久化保存
- 为后续工具调用、Agent 编排预留结构

## 推荐上线架构

- 前端：`Railway`
- 后端：`Railway`
- 域名：`Cloudflare Registrar`
- 第一步持久化方案：`Railway Volume + SQLite`
- 第二步持久化方案：迁移到 `Postgres`

推荐域名拆分：

- 前端：`app.example.com` 或 `www.example.com`
- 后端：`api.example.com`

## 现在做了什么

1. 前端已经支持通过 `VITE_API_BASE_URL` 指向生产后端地址。
2. 后端已经补齐 `Dockerfile` 和 `.dockerignore`，可以直接作为 Railway Web Service 部署。
3. 后端 SQLite 路径已经改成环境变量 `SQLITE_PATH` 可配置，便于在 Railway 上挂 volume。
4. 后端 CORS 默认本地开发端口已对齐到 `5174`，生产环境可通过 `CORS_ORIGINS_RAW` 收口。
5. `frontend/.env.example` 和 `python/.env.example` 已补成可用于本地和上线的模板。
6. 文档已经改成围绕 `Railway + Railway + Cloudflare` 的部署方案。

## 现在要做什么

1. 把仓库推到 GitHub。
2. 在 Railway 新建后端服务，服务根目录指向 `python/`。
3. 给 Railway 服务挂一个 volume，挂载路径建议用 `/data`。
4. 在 Railway 配置环境变量：
   `OPENAI_API_KEY`
   `OPENAI_BASE_URL`
   `OPENAI_MODEL`
   `ASSISTANT_SYSTEM_PROMPT`
   `CORS_ORIGINS_RAW`
   `SQLITE_PATH=/data/agent_demo.db`
5. 在 Railway 生成公开域名，先确认 `https://<your-backend>/health` 可访问。
6. 在 Railway 新建前端服务，服务根目录指向 `frontend/`。
7. 在 Railway 配置 `VITE_API_BASE_URL=https://<your-backend-domain>`。
8. 部署前端服务后，先用 Railway 提供的公开域名联通前后端。
9. 前后端都跑通后，再购买域名并绑定 `app.` / `api.` 子域名。

## 接下来要做什么

1. 把数据库从 `SQLite + Volume` 升级到 `Postgres`，避免单机 volume 成为长期瓶颈。
2. 给后端增加最基本的鉴权和接口限流，避免公开地址被滥用。
3. 增加日志、错误监控和最小告警。
4. 补一份真正面向生产的环境变量清单和回滚说明。
5. 如果要继续做 Agent，下一步再补工具调用、任务编排和可观测性。

## 当前部署注意事项

1. 你现在的后端仍然是 SQLite，所以第一版上线更适合学习和 demo，不适合高并发生产。
2. Railway volume 方案适合当前阶段，但它本质上仍是单实例思路。
3. 自定义域名不用一开始就买，先用平台送的域名把链路跑通更稳。
4. 前端一定要等后端地址稳定后，再绑定 `VITE_API_BASE_URL` 和生产 CORS。
5. 前端在 Railway 上本质是一个静态产物加 Node 进程，首版上线够用，但不是极致静态分发方案。

## 本地启动

```bash
# 前端
cd frontend
npm install
npm run dev
```

```bash
# 后端
cd python
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8001
```

## 文档维护约定

1. 当前仓库中的主要源码目录都已补 `README.md`。
2. 以后只要某个目录下的职责、结构、关键逻辑、操作方式发生变化，修改代码时必须同步更新该目录下的 `README.md`。
3. 后续 AI 继续修改本仓库时，必须把“更新对应目录 README”视为同一项工作的一部分，而不是可选项。
