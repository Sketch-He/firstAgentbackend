import json
from collections.abc import AsyncIterator
from typing import Any

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from app.core.config import get_settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse


class LLMServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: AsyncOpenAI | None = None

    def ensure_configured(self) -> None:
        if not self.settings.openai_api_key.strip():
            raise LLMServiceError(
                "未检测到 DeepSeek API Key，请先在 python/.env 中配置 OPENAI_API_KEY。",
                status_code=500
            )

    def validate_request(self, request: ChatRequest) -> None:
        if not any(message.role == "user" for message in request.messages):
            raise LLMServiceError("至少需要一条用户消息后才能发起对话。", status_code=400)

    async def generate_reply(self, request: ChatRequest) -> ChatResponse:
        self.ensure_configured()
        self.validate_request(request)

        try:
            # 这里是真正发起 DeepSeek 对话请求的地方。
            completion = await self._get_client().chat.completions.create(
                model=self.settings.openai_model,
                messages=self._build_messages(request),
                stream=False
            )
        except RateLimitError as exc:
            raise LLMServiceError("模型请求过于频繁，请稍后重试。", status_code=429) from exc
        except APIConnectionError as exc:
            raise LLMServiceError(
                "无法连接到 DeepSeek 服务，请检查网络、代理或接口地址配置。",
                status_code=502
            ) from exc
        except APIStatusError as exc:
            raise LLMServiceError(
                f"DeepSeek 服务返回异常状态：{exc.status_code}。",
                status_code=self._normalize_status_code(exc.status_code)
            ) from exc
        except Exception as exc:
            raise LLMServiceError("调用 DeepSeek 服务时发生未预期错误。", status_code=502) from exc

        if not completion.choices:
            raise LLMServiceError("模型没有返回可用结果，请稍后重试。", status_code=502)

        choice = completion.choices[0]
        content = (choice.message.content or "").strip()

        if not content:
            raise LLMServiceError("模型返回了空内容，请稍后重试。", status_code=502)

        return ChatResponse(
            reply=ChatMessage(role="assistant", content=content),
            meta={
                "mode": "chat",
                "provider": "deepseek",
                "model": completion.model,
                "finish_reason": choice.finish_reason,
                **self._extract_usage(completion.usage)
            }
        )

    async def stream_reply(self, request: ChatRequest) -> AsyncIterator[str]:
        self.ensure_configured()
        self.validate_request(request)

        try:
            # 这里是真正发起 DeepSeek 流式请求的地方。
            stream = await self._get_client().chat.completions.create(
                model=self.settings.openai_model,
                messages=self._build_messages(request),
                stream=True
            )
        except RateLimitError:
            yield self._format_sse("error", {"message": "模型请求过于频繁，请稍后重试。", "status_code": 429})
            yield self._format_sse("done", {"finish_reason": "error"})
            return
        except APIConnectionError:
            yield self._format_sse(
                "error",
                {
                    "message": "无法连接到 DeepSeek 服务，请检查网络、代理或接口地址配置。",
                    "status_code": 502
                }
            )
            yield self._format_sse("done", {"finish_reason": "error"})
            return
        except APIStatusError as exc:
            yield self._format_sse(
                "error",
                {
                    "message": f"DeepSeek 服务返回异常状态：{exc.status_code}。",
                    "status_code": self._normalize_status_code(exc.status_code)
                }
            )
            yield self._format_sse("done", {"finish_reason": "error"})
            return
        except Exception:
            yield self._format_sse(
                "error",
                {"message": "调用 DeepSeek 服务时发生未预期错误。", "status_code": 502}
            )
            yield self._format_sse("done", {"finish_reason": "error"})
            return

        yield self._format_sse(
            "meta",
            {
                "mode": "stream",
                "provider": "deepseek",
                "model": self.settings.openai_model
            }
        )

        finish_reason = "stop"
        has_content = False

        async for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta.content or ""

            if delta:
                has_content = True
                yield self._format_sse("message", {"delta": delta})

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        if not has_content:
            yield self._format_sse("error", {"message": "模型返回了空内容。", "status_code": 502})
            yield self._format_sse("done", {"finish_reason": "error"})
            return

        yield self._format_sse("done", {"finish_reason": finish_reason})

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            # DeepSeek 提供 OpenAI 兼容接口，所以这里直接使用 openai SDK，
            # 通过 base_url 指向 DeepSeek 网关。
            self._client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
                timeout=self.settings.request_timeout_seconds
            )

        return self._client

    def _build_messages(self, request: ChatRequest) -> list[dict[str, str]]:
        normalized_messages: list[dict[str, str]] = []
        seen_user_message = False

        if self.settings.assistant_system_prompt.strip():
            # 系统提示词统一从配置进入，避免把 prompt 硬编码在路由里。
            normalized_messages.append(
                {
                    "role": "system",
                    "content": self.settings.assistant_system_prompt
                }
            )

        for message in request.messages:
            # 前端欢迎语属于 UI 占位，不应在首次提问前参与模型上下文。
            if message.role == "assistant" and not seen_user_message:
                continue

            # 当前消息结构还未支持 tool_call_id，工具消息先不透传给模型。
            if message.role == "tool":
                continue

            if message.role == "user":
                seen_user_message = True

            normalized_messages.append(
                {
                    "role": message.role,
                    "content": message.content
                }
            )

        return normalized_messages

    @staticmethod
    def _extract_usage(usage: Any) -> dict[str, int]:
        if usage is None:
            return {}

        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0)
        }

    @staticmethod
    def _normalize_status_code(status_code: int | None) -> int:
        if isinstance(status_code, int) and 400 <= status_code <= 599:
            return status_code

        return 502

    @staticmethod
    def _format_sse(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
