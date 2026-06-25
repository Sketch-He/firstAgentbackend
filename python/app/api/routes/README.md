# python/app/api/routes 目录说明

## 目录职责

这个目录存放具体接口定义。

## 当前文件

- `health.py`：健康检查接口
- `chat.py`：普通聊天和流式聊天接口（支持懒创建会话、整轮持久化、partial reply 保留）
- `conversations.py`：会话 CRUD REST API（列表、创建、详情、更新标题、删除、删除上一轮）

## 统一响应格式

所有 JSON 接口统一返回 `ApiResponse` 包装：

```json
{ “code”: 0, “message”: “ok”, “data”: { ... } }
```

错误通过抛出 `ApiError` 实现，全局异常处理器会自动转换为统一格式。

流式接口（`POST /api/chat/stream`）保持 SSE 协议不变，通过 `error` 事件传递错误信息。

## 当前关键逻辑

1. `chat.py` 会先做参数和配置检查，再决定是复用已有会话还是懒创建新会话。
2. 普通接口返回 `ApiResponse` 包装的 JSON。
3. 流式接口返回 `text/event-stream`，并在 `meta/done` 事件中附带会话摘要。
4. 流式接口会在服务端统一持久化本轮用户消息和助手回复；中断时如果已有 partial assistant 内容，也会保留。
5. `conversations.py` 除了基本 CRUD，还提供”删除上一轮消息”接口，供前端重试时使用。

## 协作约定

1. 新增或调整路由时，必须同步更新本文件。
2. 如果接口协议变更，也要补充到这里。
3. 新增接口必须返回 `ApiResponse` 包装，错误使用 `ApiError` 抛出。
