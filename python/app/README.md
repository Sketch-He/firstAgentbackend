# python/app 目录说明

## 目录职责

这个目录是 Python 服务端核心源码，按 API、配置、数据模型、服务层分层组织。

## 当前结构

- `api/`：路由入口与 HTTP 层
- `core/`：配置与基础能力
- `schemas/`：Pydantic 数据模型
- `services/`：聊天服务与后续 Agent 编排

## 当前关键逻辑

1. 普通聊天请求走 `/api/chat`
2. 流式聊天请求走 `/api/chat/stream`
3. 真实 DeepSeek 兼容调用在 `services/llm.py`

## 协作约定

1. 只要目录结构、分层职责或路由入口变化，必须同步更新本文件。
2. 后续 AI 在新增模块时，需要判断是否应新增子目录 README。
