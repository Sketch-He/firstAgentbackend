# frontend/src/lib 目录说明

## 目录职责

这个目录放接口访问和底层能力封装，避免页面和 composable 直接处理过多请求细节。

## 当前文件

- `chatApi.ts`：普通 JSON 请求、SSE 流解析、统一 ApiResponse 解析、文档管理 API、RAG 聊天 API
- `markdown.ts`：前端本地 Markdown 解析与安全 HTML 渲染辅助

## 当前关键逻辑

1. 所有与聊天后端相关的请求地址统一从这里出。
2. 后端返回统一的 `{ code, message, data }` 格式，前端通过 `unwrapResponse` 解析：`code === 0` 时返回 `data`，否则抛出 `ApiError`。
3. `ApiError` 继承自 `Error`，额外携带 `code` 属性，方便上层按错误码做差异化处理。
4. SSE 使用 `fetch` + `ReadableStream` + 自定义事件解析，不依赖浏览器原生 `EventSource`。
5. 这样做的原因是 `POST /api/chat/stream` 需要携带请求体，原生 `EventSource` 不适合当前场景。
6. 当前本地开发默认通过 Vite 代理转发到 `127.0.0.1:8001`，用于避开旧的 `8000` 端口冲突。
7. 生产环境通过 `VITE_API_BASE_URL` 指向独立后端域名；未配置时默认走同源相对路径。
8. 流式请求当前支持 `AbortController` 中断，供前端实现”停止生成”。
9. 会话相关接口包括列表、详情、删除、重试前删除上一轮；真正的 assistant 持久化已经收口到后端流式接口中。
10. Markdown 渲染当前不依赖第三方库，先覆盖标题、列表、引用、链接、行内代码和 fenced code block。
11. 文档管理 API 包括上传（`multipart/formax-data`）、列表、详情、删除、重试；上传使用 `FormData` 而非 JSON。
12. RAG 聊天 API（`streamRagChat`）复用 SSE 流式模式，额外支持 `source` 事件返回检索来源。
13. SSE 解析器现在支持 `meta`、`message`、`error`、`source`、`done` 五种事件类型。

## 协作约定

1. 只要接口协议、请求方式、SSE 解析规则变化，必须同步更新本文件。
2. 如果新增其他 API 模块，也要在这里补说明。
