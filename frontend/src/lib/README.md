# frontend/src/lib 目录说明

## 目录职责

这个目录放接口访问和底层能力封装，避免页面和 composable 直接处理过多请求细节。

## 当前文件

- `chatApi.ts`：健康检查、普通 JSON 请求、SSE 流解析
- `markdown.ts`：前端本地 Markdown 解析与安全 HTML 渲染辅助

## 当前关键逻辑

1. 所有与聊天后端相关的请求地址统一从这里出。
2. SSE 使用 `fetch` + `ReadableStream` + 自定义事件解析，不依赖浏览器原生 `EventSource`。
3. 这样做的原因是 `POST /api/chat/stream` 需要携带请求体，原生 `EventSource` 不适合当前场景。
4. 当前本地开发默认通过 Vite 代理转发到 `127.0.0.1:8001`，用于避开旧的 `8000` 端口冲突。
5. 流式请求当前支持 `AbortController` 中断，供前端实现“停止生成”。
6. Markdown 渲染当前不依赖第三方库，先覆盖标题、列表、引用、链接、行内代码和 fenced code block。

## 协作约定

1. 只要接口协议、请求方式、SSE 解析规则变化，必须同步更新本文件。
2. 如果新增其他 API 模块，也要在这里补说明。
