# python/app/schemas 目录说明

## 目录职责

这个目录存放服务端请求和响应的数据模型。

## 当前文件

- `chat.py`：聊天请求（含可选 `conversation_id`）、聊天响应、健康检查响应
- `conversation.py`：会话创建/更新请求、会话摘要、单条消息输出、会话详情（含消息列表）
- `response.py`：统一 API 响应包装 `ApiResponse[T]` 和业务错误码 `ErrorCode`
- `document.py`：文档输出模型、文档列表响应、RAG 聊天请求、RAG 来源模型

## 统一响应格式

所有 JSON 接口统一返回以下格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

- `code`: 0 = 成功，非 0 = 业务错误码（见 `ErrorCode` 类）
- `message`: 人类可读的提示信息
- `data`: 业务数据（成功时），null（失败时）

## 协作约定

1. 只要接口字段变化，必须同步更新本文件。
2. 后续 AI 改路由协议时，要先确认这里的模型是否同步修改。
3. 新增接口必须返回 `ApiResponse` 包装，错误使用 `ApiError` 抛出。
