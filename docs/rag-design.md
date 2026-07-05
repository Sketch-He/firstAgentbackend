# RAG 知识库功能设计文档（2026版）

> 基于 2026 年最新技术趋势和 LangChain 官方最佳实践

## 概述

为 AI 聊天工具添加知识库功能，支持用户上传文档，基于文档内容进行问答。采用 2026 年最新的 **Agentic RAG** 架构，结合**循环工程**和**程序化编排**理念。

## 技术架构

### 2026 年 Agentic RAG 架构

```
用户提问
    ↓
┌─────────────────────────────────────────────────────────┐
│                    Agent 控制器                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 问题分析    │→ │ 路由决策    │→ │ 结果验证    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         ↓               ↓               ↓              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 简单问题    │  │ 需要检索    │  │ 质量不足    │     │
│  │ 直接回答    │  │ 向量检索    │  │ 重新检索    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    检索管道                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 向量检索    │→ │ 重排序      │→ │ 上下文拼接  │     │
│  │ (ChromaDB)  │  │ (Reranker)  │  │ (Prompt)    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    生成管道                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ LLM 生成    │→ │ 质量检查    │→ │ 流式输出    │     │
│  │ (DeepSeek)  │  │ (可选)      │  │ (SSE)       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 技术选型

### 核心组件

| 组件 | 方案 | 理由 |
|------|------|------|
| 向量数据库 | **ChromaDB** | 本地文件存储，无需部署，适合起步 |
| 文档解析 | **PyPDF2 + python-docx** | 轻量，支持 PDF/Word |
| 文本分块 | **LangChain TextSplitter** | 成熟方案，支持多种分块策略 |
| 向量化 | **OpenAI text-embedding-3-small** | 性价比高，质量好 |
| LLM | **DeepSeek** | 复用现有能力 |
| 重排序 | **Cohere Rerank**（可选） | 提升检索质量 |

### 2026 年新增考虑

| 技术 | 优先级 | 说明 |
|------|--------|------|
| **Prompt Caching** | 高 | 降低 80% token 成本 |
| **Agent Memory** | 中 | 短期+长期记忆 |
| **循环工程** | 中 | 多层次 Agent 循环 |
| **程序化编排** | 低 | 

 |

## 数据模型

### 文档表 (documents)

```sql
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'processing',
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
```

### 向量存储 (ChromaDB)

```
Collection: knowledge_base
Fields:
  - document: 文本片段
  - embedding: 向量
  - metadata:
    - user_id: 用户ID
    - document_id: 文档ID
    - chunk_index: 片段索引
    - filename: 文件名
    - created_at: 创建时间
```

## API 设计

### 文档管理

```
POST   /api/documents/upload      上传文档
GET    /api/documents              列出用户文档
GET    /api/documents/{id}         获取文档详情
DELETE /api/documents/{id}         删除文档
POST   /api/documents/{id}/retry   重新处理失败文档
```

### RAG 聊天

```
POST   /api/chat/rag              RAG聊天 (流式)
```

### 请求/响应格式

```typescript
// RAG 聊天请求
interface RagChatRequest {
  messages: ChatMessage[];
  conversation_id?: string;
  rag_mode: 'auto' | 'always' | 'never';  // 2026: Agent 自动决策
  top_k?: number;                          // 检索片段数
}

// RAG 聊天响应（流式）
interface RagStreamEvent {
  event: 'meta' | 'message' | 'source' | 'done' | 'error';
  data: {
    // meta: 模型信息
    // message: 增量文本
    // source: 来源文档（2026: 实时返回）
    // done: 完成信号
    // error: 错误信息
  };
}
```

## 分块策略（2026 最佳实践）

### 推荐参数

```python
CHUNK_SIZE = 500        # tokens
CHUNK_OVERLAP = 50      # tokens
SEPARATORS = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
```

### 分块策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **固定大小** | 简单 | 可能切断语义 | 快速原型 |
| **递归分割** | 保留语义 | 计算量稍大 | **推荐** |
| **语义分割** | 最佳质量 | 计算量大 | 高质量需求 |
| **文档结构** | 保留格式 | 依赖文档结构 | 结构化文档 |

## 实现步骤

### 第一阶段：基础 RAG（MVP）

1. 新增依赖：chromadb, langchain, pypdf2, python-docx
2. 创建 documents 表
3. 实现文档解析服务
4. 实现向量化和存储服务
5. 实现检索服务
6. 新增 API 路由
7. 前端：文档上传界面
8. 前端：RAG 聊天入口

### 第二阶段：Agentic RAG

1. 实现 Agent 控制器
2. 实现问题分析和路由决策
3. 实现结果验证和重试机制
4. 实现来源追踪和引用

### 第三阶段：优化和扩展

1. Prompt Caching（降低 80% 成本）
2. 混合检索（向量 + BM25）
3. 重排序（Cohere Rerank）
4. Agent Memory（长期记忆）

## 目录结构

```
python/app/
├── api/routes/
│   ├── documents.py      # 文档管理路由
│   └── chat.py           # RAG 聊天路由
├── services/
│   ├── document.py       # 文档解析服务
│   ├── vector_store.py   # 向量存储服务
│   ├── rag.py            # RAG 检索服务
│   └── agent.py          # Agent 控制器（第二阶段）
├── schemas/
│   └── document.py       # 文档相关 schema
└── core/
    └── config.py         # RAG 配置
```

## 配置项

```python
# RAG 配置
EMBEDDING_API_KEY: str = ""
EMBEDDING_MODEL: str = "text-embedding-3-small"
CHROMA_PERSIST_DIR: str = "./chroma_db"
RAG_CHUNK_SIZE: int = 500
RAG_CHUNK_OVERLAP: int = 50
RAG_TOP_K: int = 3

# 2026 新增配置
RAG_PROMPT_CACHE_ENABLED: bool = True    # 启用提示缓存
RAG_AGENT_MODE: str = "auto"             # Agent 模式：auto/always/never
RAG_MAX_RETRIES: int = 2                 # 最大重试次数
```

## Prompt Caching 实现（2026 关键优化）

```python
# 系统提示词（固定部分，可缓存）
SYSTEM_PROMPT = """你是一个知识库助手。基于以下参考资料回答用户问题。

规则：
1. 优先使用参考资料中的内容
2. 如果参考资料中没有相关信息，说明后基于通用知识回答
3. 引用来源时标注文档名和片段索引

参考资料：
{context}
"""

# 用户问题（变化部分）
USER_PROMPT = "{question}"

# 2026: Deep Agents 自动启用提示缓存
# 相同前缀的提示只计费新增部分，降低 80% 成本
```

## Agent Memory 设计（2026）

```python
class AgentMemory:
    """2026: 三层记忆架构"""

    def __init__(self):
        self.short_term = []      # 短期记忆：当前对话
        self.long_term = VectorStore()  # 长期记忆：跨会话
        self.working = {}         # 工作记忆：任务状态

    def add_to_short_term(self, message):
        """添加到短期记忆"""
        self.short_term.append(message)
        # 限制长度，避免 token 超限
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-10:]

    def save_to_long_term(self, key, value):
        """保存到长期记忆"""
        self.long_term.add(key, value)

    def get_context(self, query):
        """获取相关上下文"""
        # 短期记忆 + 长期记忆检索
        short_context = self.short_term[-5:]
        long_context = self.long_term.search(query)
        return short_context + long_context
```

## 成本估算

| 项目 | 成本 | 说明 |
|------|------|------|
| Embedding API | ~$0.02/1M tokens | OpenAI |
| ChromaDB | 免费 | 本地存储 |
| LLM 调用 | 现有成本 | DeepSeek |
| **Prompt Caching** | **-80%** | **2026 关键优化** |

## 注意事项

1. **用户隔离**：向量检索必须按 user_id 过滤
2. **文件大小限制**：单文件 < 10MB
3. **支持格式**：PDF、Word、TXT、Markdown
4. **异步处理**：大文档上传后异步解析
5. **错误处理**：解析失败给用户明确提示
6. **Prompt Caching**：系统提示词保持固定，利用缓存
7. **来源追踪**：返回答案时附带来源文档信息

## 面试回答模板

### 问：为什么用 RAG？

> "RAG 解决了 LLM 知识截止和幻觉问题。通过检索用户文档，让 AI 基于真实数据回答，而不是编造。2026 年的 Agentic RAG 更进一步，Agent 会自主决定是否需要检索、检索什么、结果够不够好，不够就重新检索。"

### 问：技术选型？

> "我选择 ChromaDB 作为向量库，因为它轻量、本地存储、无需部署。LangChain 负责文档解析和分块。2026 年的关键优化是 Prompt Caching，可以降低 80% token 成本。未来如果需要更高质量，会加入 Cohere Rerank 做重排序。"

### 问：2026 年 RAG 有什么新趋势？

> "2026 年的核心趋势是 Agentic RAG 和循环工程。不再是简单的检索+生成，而是 Agent 主导整个流程。编排方式从工具调用转向程序化，用 Dynamic Subagents 实现可靠的多步骤管道。成本优化方面，Deep Agents 的提示缓存可以降低 80% token 消耗。"

---

*最后更新：2026-07-04*
*基于 LangChain 官方博客 2026年6-7月最新文章*
*来源：https://www.langchain.com/blog*
