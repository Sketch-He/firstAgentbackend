# AI 聊天助手 + RAG 知识库 — 项目说明文档

> 📌 **文档维护标记**：当项目功能、技术选型、架构设计发生变化时，必须同步更新本文档。

---

## 一、项目概述

一个基于 AI 的智能聊天助手，支持普通对话和基于文档的 RAG（检索增强生成）问答。用户可以上传 PDF/Word/TXT/Markdown 文档，系统会自动解析、向量化，然后基于文档内容回答问题并附带来源引用。

### 核心能力

| 能力 | 说明 |
|------|------|
| 💬 智能对话 | 基于 DeepSeek 大模型的流式对话，支持 Markdown 渲染、代码高亮 |
| 📚 知识库问答 | 上传文档后，AI 可基于文档内容回答问题，减少幻觉 |
| 🔍 来源引用 | RAG 回答时展示引用了哪些文档的哪些片段，可追溯 |
| 👤 用户隔离 | 每个用户的数据（对话、文档、向量）完全隔离 |
| 📱 响应式布局 | 桌面端侧栏布局，移动端自适应 |

---

## 二、技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ ChatPage │  │ Sidebar  │  │ Composer │  │ Knowledge│    │
│  │  聊天页  │  │ 会话列表 │  │ 输入区域 │  │ 知识面板 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         ↓              ↓            ↓             ↓         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              composables (状态管理)                   │    │
│  │     useChat · useConversation · useDocuments         │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↓                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              lib/chatApi.ts (HTTP + SSE)              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP / SSE
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  API 路由层                           │    │
│  │    chat · conversations · documents · health         │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↓              ↓             ↓                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ LLM 服务 │  │ 文档服务 │  │ RAG 服务 │                 │
│  │ DeepSeek │  │ 解析/分块│  │ 检索/生成│                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│         ↓              ↓             ↓                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ OpenAI   │  │ SQLite   │  │ ChromaDB │                 │
│  │   API    │  │  数据库  │  │ 向量数据库│                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、技术选型详解

### 前端技术栈

| 技术 | 版本 | 为什么用 | 达成效果 |
|------|------|----------|----------|
| **Vue 3** | ^3.5 | 组合式 API 适合复杂状态管理，学习成本低 | 响应式 UI，组件化开发 |
| **TypeScript** | ^5.5 | 类型安全，减少运行时错误 | 编译时发现类型问题 |
| **Vite** | ^5.4 | 极快的 HMR 和构建速度 | 开发体验好，构建快 |
| **SSE (Server-Sent Events)** | 原生 | 比 WebSocket 轻量，适合单向流式推送 | 流式输出 AI 回复，打字机效果 |
| **自定义 Markdown 解析器** | - | 无需引入第三方库，轻量可控 | 代码高亮、列表、引用渲染 |

### 后端技术栈

| 技术 | 版本 | 为什么用 | 达成效果 |
|------|------|----------|----------|
| **FastAPI** | ^0.111 | 异步高性能，自动生成 API 文档，类型校验 | RESTful API + 流式 SSE |
| **SQLite + aiosqlite** | - | 零部署，文件级数据库，适合起步阶段 | 会话和消息持久化 |
| **DeepSeek API** | OpenAI 兼容 | 国产大模型，性价比高，中文效果好 | 智能对话能力 |
| **ChromaDB** | ^0.5 | 本地文件存储的向量数据库，无需部署 | 文档向量存储和检索 |
| **LangChain TextSplitter** | ^0.3 | 成熟的文本分块方案，支持递归分割 | 语义完整的文档分块 |
| **PyPDF2 + python-docx** | - | 轻量的文档解析库 | PDF/Word 文档解析 |
| **OpenAI SDK** | ^1.35 | 统一的 Embedding API 调用 | 文本向量化 |

### RAG 技术栈

| 技术 | 为什么用 | 达成效果 |
|------|----------|----------|
| **BGE-M3 Embedding** | 中文效果最好的开源 Embedding 模型之一，支持 8192 长文本 | 高质量的中文文本向量化 |
| **ChromaDB 向量检索** | 轻量、本地存储、支持 metadata 过滤 | 按用户隔离的语义检索 |
| **递归分割策略** | 按语义边界分块（段落→句子→字符），保留上下文 | 检索时能命中完整的语义单元 |
| **SSE source 事件** | 流式返回时附带来源文档信息 | 用户可追溯答案来源 |

---

## 四、功能详解

### 4.1 智能对话

**技术实现**：
- 前端通过 `fetch` + `ReadableStream` 实现 SSE 流式接收
- 后端使用 OpenAI SDK 的 `stream=True` 模式调用 DeepSeek
- 消息持久化到 SQLite，支持会话列表、切换、删除

**达成效果**：
- 打字机效果的流式输出
- 支持中途停止生成
- 支持一键重试上一轮
- 会话历史持久保存

### 4.2 RAG 知识库

**技术实现**：

```
用户上传文档
    ↓
后台异步处理 (asyncio.create_task)
    ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  文档解析    │ →  │  文本分块    │ →  │  向量化存储  │
│ PyPDF2/docx │    │ LangChain   │    │ ChromaDB    │
└─────────────┘    └─────────────┘    └─────────────┘
                                              ↓
用户提问 → 向量检索 → 拼接上下文 → LLM 生成 → 流式输出 + 来源引用
```

**达成效果**：
- 支持 PDF/Word/TXT/Markdown 四种格式
- 文档处理不阻塞用户操作（后台异步）
- 检索时按用户隔离，不同用户的知识库互不可见
- 回答附带来源引用，可追溯

### 4.3 RAG 模式

| 模式 | 触发条件 | 适用场景 |
|------|----------|----------|
| 🤖 自动（默认） | AI 判断是否需要检索 | 日常使用，简单问题直接回答，复杂问题检索文档 |
| 📚 始终检索 | 每次都检索知识库 | 确定需要基于文档回答时 |
| 💬 纯聊天 | 不检索知识库 | 闲聊或文档无关的问题 |

---

## 五、项目结构

```
firstAgentbackend/
├── frontend/                    # 前端 Vue 3 项目
│   └── src/
│       ├── components/          # UI 组件
│       │   ├── ChatPage.vue     # 聊天主页面
│       │   ├── Sidebar.vue      # 会话侧栏 + 知识库入口
│       │   ├── Composer.vue     # 输入区 + RAG 模式切换
│       │   ├── MessageBubble.vue # 消息气泡 + 来源引用
│       │   ├── KnowledgePanel.vue # 知识库面板
│       │   └── SourceBubble.vue # 来源引用展示
│       ├── composables/         # 状态管理
│       │   ├── useChat.ts       # 聊天状态 + RAG 模式
│       │   ├── useConversation.ts # 会话列表管理
│       │   └── useDocuments.ts  # 文档管理
│       ├── lib/                 # 工具函数
│       │   ├── chatApi.ts       # HTTP + SSE API 封装
│       │   └── markdown.ts      # Markdown 解析器
│       └── types/               # TypeScript 类型定义
│
├── python/                      # 后端 FastAPI 项目
│   └── app/
│       ├── api/routes/          # API 路由
│       │   ├── chat.py          # 聊天 + RAG 聊天
│       │   ├── conversations.py # 会话 CRUD
│       │   ├── documents.py     # 文档管理
│       │   └── health.py        # 健康检查
│       ├── services/            # 业务逻辑层
│       │   ├── llm.py           # LLM 调用封装
│       │   ├── conversation.py  # 会话服务
│       │   ├── document.py      # 文档解析服务
│       │   ├── vector_store.py  # 向量存储服务
│       │   └── rag.py           # RAG 检索生成服务
│       ├── schemas/             # 数据模型
│       ├── core/                # 基础设施
│       │   ├── config.py        # 配置管理
│       │   ├── database.py      # 数据库连接
│       │   └── exceptions.py    # 异常处理
│       └── main.py              # 应用入口
│
└── docs/                        # 项目文档
    ├── rag-design.md            # RAG 设计文档
    └── project-guide.md         # 本文档
```

---

## 六、本地启动

### 环境要求

- Node.js >= 18
- Python >= 3.11

### 后端启动

```bash
cd python
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入：
#   OPENAI_API_KEY=你的 DeepSeek Key
#   EMBEDDING_API_KEY=你的硅基流动 Key
#   EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
#   EMBEDDING_MODEL=BAAI/bge-m3

uvicorn app.main:app --reload --port 8001
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5174

---

## 七、环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | - | DeepSeek API Key |
| `OPENAI_BASE_URL` | ❌ | `https://api.deepseek.com/v1` | LLM API 地址 |
| `OPENAI_MODEL` | ❌ | `deepseek-chat` | LLM 模型名 |
| `EMBEDDING_API_KEY` | ✅ | 回退到 OPENAI_API_KEY | Embedding API Key |
| `EMBEDDING_BASE_URL` | ❌ | 回退到 OPENAI_BASE_URL | Embedding API 地址 |
| `EMBEDDING_MODEL` | ❌ | `BAAI/bge-m3` | Embedding 模型名 |
| `CHROMA_PERSIST_DIR` | ❌ | `./chroma_db` | 向量库存储目录 |
| `SQLITE_PATH` | ❌ | `agent_demo.db` | SQLite 文件路径 |
| `CORS_ORIGINS_RAW` | ❌ | `http://localhost:5174` | 允许的前端来源 |
| `RAG_CHUNK_SIZE` | ❌ | `500` | 分块大小（tokens） |
| `RAG_CHUNK_OVERLAP` | ❌ | `50` | 分块重叠（tokens） |
| `RAG_TOP_K` | ❌ | `3` | 检索返回片段数 |
| `MAX_UPLOAD_SIZE_MB` | ❌ | `10` | 单文件大小限制（MB） |

---

## 八、API 接口文档

启动后端后访问 http://localhost:8001/docs 查看 Swagger 自动生成的 API 文档。

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/stream` | 普通流式聊天 |
| POST | `/api/chat/rag` | RAG 流式聊天 |
| POST | `/api/documents/upload` | 上传文档 |
| GET | `/api/documents` | 列出用户文档 |
| DELETE | `/api/documents/{id}` | 删除文档 |
| GET | `/api/conversations` | 列出会话 |
| GET | `/api/conversations/{id}` | 获取会话详情 |
| GET | `/health` | 健康检查 |

### 统一响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

### SSE 流式事件

| 事件 | 说明 |
|------|------|
| `meta` | 模型信息、会话信息 |
| `message` | 增量文本 `{"delta": "..."}` |
| `source` | 来源文档引用（RAG 模式） |
| `done` | 完成信号 |
| `error` | 错误信息 |

---

## 九、面试回答要点

### Q: 为什么用 RAG？

> RAG 解决了 LLM 的两个核心问题：**知识截止**和**幻觉**。LLM 的训练数据有截止日期，无法回答最新或私有数据的问题；而且 LLM 可能会"编造"答案。通过 RAG，我们先从用户文档中检索相关内容，再让 LLM 基于这些真实数据生成回答，大幅减少幻觉并提高准确性。

### Q: 技术选型的考量？

> **ChromaDB**：选择它是因为轻量、本地文件存储、无需部署额外服务，适合项目起步阶段。相比 Milvus/Qdrant 这类重型方案，ChromaDB 几乎零运维成本。
>
> **LangChain TextSplitter**：递归分割策略按语义边界（段落→句子→字符）切分，比固定大小分割更好地保留上下文完整性。
>
> **BGE-M3 Embedding**：中文效果最好的开源 Embedding 模型之一，支持 8192 长文本和 100+ 语言，在 MTEB 排行榜长期位居前列。
>
> **SSE vs WebSocket**：AI 回答是典型的单向流式场景，SSE 比 WebSocket 更轻量，且原生支持 HTTP，无需额外协议升级。

### Q: 项目的亮点？

1. **完整的 RAG 流程**：从文档上传、解析、分块、向量化、检索到生成，端到端实现
2. **用户数据隔离**：向量检索按 `user_id` 过滤，不同用户的知识库完全隔离
3. **异步文档处理**：上传后后台异步处理，不阻塞用户操作
4. **来源可追溯**：RAG 回答附带来源引用，用户可验证答案的准确性
5. **流式体验**：SSE 流式输出 + 打字机效果，用户体验好
6. **多 RAG 模式**：自动/始终检索/纯聊天三种模式，灵活适配不同场景

### Q: 遇到的技术挑战？

1. **SSE 流式解析**：浏览器原生 EventSource 不支持 POST 请求体，需要用 `fetch` + `ReadableStream` 手动解析
2. **文档异步处理**：使用 `asyncio.create_task` 实现后台处理，需要处理失败状态和错误信息回传
3. **向量检索用户隔离**：ChromaDB 的 metadata 过滤支持 `where` 条件，实现了按用户隔离的语义检索
4. **RAG 模式判断**：auto 模式使用简单启发式（问候语检测），后续可升级为 Agent 决策

---

## 十、后续规划

### 第二阶段：Agentic RAG

- [ ] Agent 控制器（问题分析→路由决策→结果验证）
- [ ] 检索结果质量评估，不足时自动重新检索
- [ ] 更智能的 RAG 模式判断

### 第三阶段：优化和扩展

- [ ] Prompt Caching（降低 80% token 成本）
- [ ] 混合检索（向量 + BM25 关键词检索）
- [ ] 重排序（Cohere Rerank 提升检索质量）
- [ ] Agent Memory（短期+长期记忆）

### 生产化

- [ ] 数据库从 SQLite 迁移到 Postgres
- [ ] 用户认证和接口限流
- [ ] 日志、监控和告警
- [ ] Docker Compose 一键部署

---

## 十一、文档维护约定

> ⚠️ **本文档需要随项目功能更新而同步更新。**
>
> 以下情况必须更新本文档：
> 1. 新增或移除核心功能
> 2. 技术选型发生变化
> 3. API 接口发生变更
> 4. 项目结构发生调整
> 5. 环境变量发生变更
> 6. 部署方式发生变化

---

*最后更新：2026-07-05*
*维护者：hql*
