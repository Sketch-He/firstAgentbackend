# DeepSeek 接入与 SSE 阅读说明

## 这份文档看什么

这份文档专门解释当前项目里与 DeepSeek 接入最相关的 4 个文件：

1. `python/app/core/config.py`
2. `python/app/api/routes/chat.py`
3. `python/app/services/llm.py`
4. `frontend/src/lib/chatApi.ts`

阅读顺序建议：

1. 先看 `config.py`，知道配置从哪里来
2. 再看 `chat.py`，知道请求先进入哪里
3. 再看 `llm.py`，知道哪里真正调用 DeepSeek
4. 最后看 `chatApi.ts`，知道前端怎么接收流式内容

---

## 先回答你的问题

### 为什么接口响应不是普通 JSON，而是这种：

```text
event: meta
data: {"mode": "stream", "provider": "deepseek", "model": "deepseek-chat"}

event: message
data: {"delta": "我是"}

event: message
data: {"delta": " Deep"}
```

因为你现在调用的不是普通接口，而是 **SSE 流式接口**：

- 路径是 `/api/chat/stream`
- 返回类型是 `text/event-stream`
- 它的目标不是“一次性返回完整结果”
- 它的目标是“模型一边生成，前端一边收到”

所以它返回的是一段一段的事件流，而不是一次性 JSON。

### 这种格式是什么意思

SSE 的基本格式就是：

```text
event: 事件名
data: 事件数据

event: 事件名
data: 事件数据
```

每个事件块之间用一个空行分隔。

当前项目里定义了几种事件：

- `meta`
  - 表示这次流式请求的元信息
  - 例如模型名、模式、provider
- `message`
  - 表示模型新吐出来的一小段文本
  - 当前字段叫 `delta`
- `error`
  - 表示流式过程中发生错误
- `done`
  - 表示流式输出结束

所以你看到的不是“异常响应”，而是 **SSE 协议本来就该长这样**。

如果这是普通接口 `/api/chat`，返回的才会是这种完整 JSON：

```json
{
  "reply": {
    "role": "assistant",
    "content": "完整回答"
  },
  "meta": {
    "provider": "deepseek"
  }
}
```

---

## 1. `python/app/core/config.py`

文件作用：

- 统一管理后端配置
- 从 `python/.env` 读取 DeepSeek 配置
- 提供给其他模块调用

### 第 7-13 行

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

解释：

- 这里定义了一个 `Settings` 配置类
- `env_file=".env"` 表示真实运行配置从 `python/.env` 读取
- 所以后端能不能连上 DeepSeek，首先取决于 `.env` 里有没有正确的 key

### 第 15-24 行

这些是当前项目最关键的配置项：

- `app_name`
  - FastAPI 服务名
- `api_prefix`
  - 接口统一前缀，现在是 `/api`
- `cors_origins_raw`
  - 允许哪些前端地址访问后端
- `openai_api_key`
  - 实际用来请求 DeepSeek 的密钥
- `openai_base_url`
  - 指向 DeepSeek 的 OpenAI 兼容地址
- `openai_model`
  - 当前默认模型名
- `assistant_system_prompt`
  - 系统提示词
- `request_timeout_seconds`
  - 请求超时秒数

其中最关键的是：

```python
openai_base_url: str = "https://api.deepseek.com/v1"
openai_model: str = "deepseek-chat"
```

这说明：

- 你虽然用的是 `openai` Python SDK
- 但实际请求发向的是 DeepSeek 的兼容接口

### 第 26-37 行

这部分只是在处理 CORS 配置格式：

- `.env` 里写的是逗号分隔字符串
- 代码里把它转成 `list[str]`
- 然后 `main.py` 里给 FastAPI 的 CORS 中间件使用

### 第 40-42 行

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

解释：

- 整个项目里其他地方不会直接手动读 `.env`
- 都通过 `get_settings()` 拿配置
- `@lru_cache` 的意思是：配置只创建一次，后面复用

---

## 2. `python/app/api/routes/chat.py`

文件作用：

- 这是聊天接口的 HTTP 入口
- 接住前端请求
- 再转交给 `LLMService`

### 第 7-8 行

```python
router = APIRouter(prefix="/chat", tags=["chat"])
llm_service = LLMService()
```

解释：

- 当前这个文件里所有路由都挂在 `/chat` 下面
- 真正干活的是 `llm_service`

因为 `main.py` 里还给整个 API 加了 `/api` 前缀，所以最终完整路径是：

- 普通接口：`/api/chat`
- 流式接口：`/api/chat/stream`

### 第 11-17 行

```python
@router.post("", response_model=ChatResponse)
async def create_chat_reply(request: ChatRequest) -> ChatResponse:
```

解释：

- 这是普通接口
- 一次请求，一次完整返回
- 如果前端用这个接口，拿到的是完整 JSON

核心逻辑只有一行：

```python
return await llm_service.generate_reply(request)
```

意思是：

- HTTP 层只做入口
- 真正的模型调用在 `LLMService.generate_reply`

### 第 20-47 行

```python
@router.post("/stream")
async def stream_chat_reply(request: Request, payload: ChatRequest) -> StreamingResponse:
```

解释：

- 这是流式接口
- 它不会一次性返回完整 JSON
- 它会返回 `StreamingResponse`

第 22-29 行的 `print(...)`：

- 只是你调试用的打印
- 证明请求有没有真正进入这份后端代码

第 30-34 行：

- 先检查配置是否存在
- 再检查请求是否合法
- 如果不合法，直接抛 HTTP 错误

第 36-47 行：

```python
return StreamingResponse(
    llm_service.stream_reply(payload),
    media_type="text/event-stream",
    headers=headers
)
```

这是整个流式接口最关键的一段。

意思是：

- `llm_service.stream_reply(payload)` 是一个异步生成器
- 它会不断 `yield` 一段一段的文本
- FastAPI 会把这些段按流式方式发给前端
- `media_type="text/event-stream"` 明确告诉浏览器：这是 SSE，不是普通 JSON

这就是为什么你看到响应长成：

```text
event: message
data: {"delta": "我是"}
```

---

## 3. `python/app/services/llm.py`

文件作用：

- 这里是真正接 DeepSeek 的核心文件
- 普通对话和流式对话都在这里完成

### 第 11-15 行

```python
class LLMServiceError(Exception):
```

解释：

- 这是自定义异常
- 后面如果模型调用失败，会统一转成这个异常
- `chat.py` 再把它转成 HTTP 错误返回给前端

### 第 18-21 行

```python
class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: AsyncOpenAI | None = None
```

解释：

- 服务初始化时先拿配置
- `_client` 先不创建，等第一次请求来了再懒加载

### 第 23-32 行

这两段是基础校验：

- `ensure_configured()`
  - 检查 API Key 有没有配置
- `validate_request()`
  - 检查至少有一条 `user` 消息

这两步的作用是：尽量在真正调用 DeepSeek 之前就把低级错误挡住。

### 第 34-78 行：普通调用

这是普通接口真正调用模型的逻辑。

最关键的一行在第 40 行：

```python
completion = await self._get_client().chat.completions.create(
```

这就是当前项目里 **真正请求 DeepSeek** 的地方。

它做了三件事：

1. 通过 `_get_client()` 拿到 DeepSeek 客户端
2. 把消息数组发给模型
3. 用 `stream=False` 一次性拿完整结果

第 41-43 行：

```python
model=self.settings.openai_model,
messages=self._build_messages(request),
stream=False
```

解释：

- 模型名从配置里拿
- 消息体先通过 `_build_messages()` 做清洗
- `stream=False` 表示普通模式

第 45-58 行：

- 这一段是各种错误处理
- 限流、网络失败、服务状态异常、未知异常都分别处理

第 69-78 行：

这里把 DeepSeek 返回内容整理成统一的 `ChatResponse`

```python
return ChatResponse(
    reply=ChatMessage(role="assistant", content=content),
    meta={...}
)
```

所以普通接口最终返回的是标准 JSON 对象。

### 第 80-154 行：流式调用

这个函数是 SSE 的核心。

最关键的一行在第 86 行：

```python
stream = await self._get_client().chat.completions.create(
```

和普通接口不同的是这里：

```python
stream=True
```

意思是：

- 不一次性返回完整回答
- 而是让模型边生成边吐增量内容

第 123-130 行：

```python
yield self._format_sse(
    "meta",
    {
        "mode": "stream",
        "provider": "deepseek",
        "model": self.settings.openai_model
    }
)
```

解释：

- 流开始前先发一个 `meta` 事件
- 告诉前端：这次是流式，provider 是 deepseek，模型名是什么

第 135-147 行：

```python
async for chunk in stream:
```

解释：

- 这里开始遍历 DeepSeek 返回的每个增量块
- 每个 `chunk` 都可能只是一小段文本

```python
delta = choice.delta.content or ""
```

这里取出模型新增的一小段内容。

```python
yield self._format_sse("message", {"delta": delta})
```

这一步非常关键：

- 后端不是直接把整段回答返回给前端
- 而是每拿到一点点 `delta`
- 就包装成一个 SSE `message` 事件发出去

所以你才会看到：

```text
event: message
data: {"delta": "我是"}
```

后面再来一段：

```text
event: message
data: {"delta": " Deep"}
```

这本质上就是“模型每吐一点，后端就转发一点”。

第 154 行：

```python
yield self._format_sse("done", {"finish_reason": finish_reason})
```

解释：

- 流结束时发一个 `done`
- 告诉前端这次生成结束了

### 第 156-166 行：客户端初始化

```python
self._client = AsyncOpenAI(
    api_key=self.settings.openai_api_key,
    base_url=self.settings.openai_base_url,
    timeout=self.settings.request_timeout_seconds
)
```

这段就是 DeepSeek 客户端初始化的关键。

重点理解：

- SDK 是 `openai`
- 但 `base_url` 是 `https://api.deepseek.com/v1`
- 所以实际请求打到的是 DeepSeek

### 第 168-200 行：消息清洗

`_build_messages()` 的作用：

- 给模型补系统提示词
- 过滤不该传的消息
- 把前端消息整理成模型能接受的格式

当前做了两件重要事情：

1. 过滤前端初始欢迎语
   - 避免 UI 占位文案污染真实上下文
2. 过滤 `tool` 消息
   - 因为当前还没上完整 tool_call 协议

### 第 220-222 行：SSE 格式化

```python
return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
```

这就是你看到那种响应格式的直接来源。

它明确把每一段内容拼成：

```text
event: xxx
data: {...}

```

这不是“长得不像接口”，而是 **它本来就是流式事件协议**。

---

## 4. `frontend/src/lib/chatApi.ts`

文件作用：

- 这是前端请求后端的统一入口
- 普通请求和流式请求都在这里

### 第 11 行

```ts
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
```

解释：

- 前端接口基地址从环境变量拿
- 如果为空，就走相对路径
- 本地开发时通常配合 Vite 代理使用

### 第 14-31 行：普通 JSON 请求

`postJson()` 是一个小封装：

- 发 POST
- 自动转 JSON
- 自动处理非 200 错误

### 第 33-35 行

```ts
export function createChatReply(payload: ChatRequest): Promise<ChatResponse> {
  return postJson<ChatResponse>("/api/chat", payload);
}
```

这说明：

- 如果前端要走普通接口
- 就会请求 `/api/chat`
- 最终拿到一个标准 JSON 对象

### 第 59-119 行：前端流式请求

这是前端接 SSE 的核心。

第 67 行：

```ts
const response = await fetch(`${apiBaseUrl}/api/chat/stream`, {
```

说明：

- 前端流式走的是 `/api/chat/stream`
- 用的是 `fetch`
- 不是浏览器原生 `EventSource`

为什么不用 `EventSource`？

因为当前接口是 `POST`，而原生 `EventSource` 只适合 `GET`。

第 71 行：

```ts
Accept: "text/event-stream",
```

这一步是在明确告诉后端：

- 我想要的是 SSE 流
- 不是普通 JSON

第 82-88 行：

```ts
const reader = response.body.getReader();
const decoder = new TextDecoder("utf-8");
let buffer = "";
```

解释：

- 浏览器拿到的是字节流
- 要手动一段一段读取
- 再转成文本

第 90-112 行：

这段是在手动解析 SSE：

1. 不断读取服务端返回的数据块
2. 拼到 `buffer`
3. 按 `\n\n` 切事件块
4. 每个事件块交给 `parseSseChunk()`

### 第 121-160 行：解析 SSE 事件

这里是前端把 SSE 文本协议还原成 JS 对象的地方。

例如服务端给的是：

```text
event: message
data: {"delta":"我是"}
```

这里会解析成：

- `eventName = "message"`
- `payload = { delta: "我是" }`

然后调用：

```ts
handlers.onMessage(payload as StreamMessageEvent);
```

于是页面就能把 `"我是"` 拼到 assistant 消息末尾。

### 第 115-118 行：为什么支持停止生成

```ts
return {
  abort: () => abortController.abort(),
  completed
};
```

解释：

- 这里把 `AbortController` 暴露回去
- `useChat.ts` 拿到它后，就能实现“停止生成”

---

## 最后一遍总结链路

### 普通接口链路

1. 前端请求 `/api/chat`
2. `chat.py -> create_chat_reply()`
3. `llm.py -> generate_reply()`
4. `AsyncOpenAI(...).chat.completions.create(..., stream=False)`
5. 一次性返回完整 JSON

### 流式接口链路

1. 前端请求 `/api/chat/stream`
2. `chat.py -> stream_chat_reply()`
3. `llm.py -> stream_reply()`
4. `AsyncOpenAI(...).chat.completions.create(..., stream=True)`
5. DeepSeek 不断返回增量 `chunk`
6. 后端把每个增量包装成 SSE：
   - `event: message`
   - `data: {"delta":"..."}`
7. 前端 `chatApi.ts` 解析 SSE
8. 页面把每个 `delta` 逐段拼接成完整回答

---

## 你现在最该记住的两句话

1. **DeepSeek 真正被调用的位置在 `python/app/services/llm.py` 里的 `chat.completions.create(...)`**
2. **你看到那种 `event: ... / data: ...` 的响应，不是异常，而是 SSE 流式协议本来就这样**
