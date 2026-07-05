# python/app/services 目录说明

## 目录职责

这个目录承载服务层逻辑，负责真正执行业务，而不是处理 HTTP 细节。

## 当前文件

- `llm.py`：真实 DeepSeek 兼容聊天调用、流式输出、错误包装
- `agent.py`：后续 Agent 编排入口占位
- `conversation.py`：会话 CRUD（创建、列表、详情、更新标题、删除）、消息保存、自动标题、上一轮删除
- `document.py`：文档解析服务（PDF/Word/TXT/Markdown）、文本分块、文档记录 CRUD
- `vector_store.py`：向量存储服务（ChromaDB）、文档向量化、向量检索
- `rag.py`：RAG 检索增强生成服务、流式 RAG 聊天

## 当前关键逻辑

1. `llm.py` 中 `generate_reply` 负责普通聊天响应。
2. `llm.py` 中 `stream_reply` 负责 SSE 增量输出。
3. 这里会过滤前端欢迎语，避免把 UI 占位文本误送给模型。
4. `conversation.py` 使用 SQLite 持久化会话和消息，自动从用户首条消息生成会话标题。
5. 重试上一轮时，会通过服务层先删除数据库中最后一轮用户/助手消息，再重新发起生成。
6. `document.py` 使用 LangChain `RecursiveCharacterTextSplitter` 进行文本分块，支持 PDF/Word/TXT/Markdown 格式。
7. `vector_store.py` 使用 ChromaDB 进行向量存储，支持按 `user_id` 隔离的向量检索。
8. `rag.py` 实现 Agentic RAG 流程：根据 `rag_mode` 决定是否检索 → 向量检索 → 拼接上下文 → LLM 流式生成。

## 协作约定

1. 只要模型调用方式、错误处理、流式协议、Agent 分层变化，必须同步更新本文件。
2. 后续 AI 修改大模型接入方式时，必须连同本文件一起更新。
