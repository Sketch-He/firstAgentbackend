import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import ApiError
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.response import ApiResponse, ErrorCode, HTTP_STATUS_TO_CODE
from app.services.conversation import ConversationService
from app.services.llm import LLMService, LLMServiceError

router = APIRouter(prefix="/chat", tags=["chat"])
llm_service = LLMService()
conversation_service = ConversationService()


def _get_user_id(x_user_id: str = Header(default="")) -> str:
    if not x_user_id:
        raise ApiError(code=ErrorCode.BAD_REQUEST, message="缺少 X-User-Id 请求头。", status_code=400)
    return x_user_id


@router.post("")
async def create_chat_reply(request: ChatRequest) -> ApiResponse[ChatResponse]:
    # 这个接口用于普通一次性返回。
    try:
        result = await llm_service.generate_reply(request)
        return ApiResponse.success(data=result)
    except LLMServiceError as exc:
        code = HTTP_STATUS_TO_CODE.get(exc.status_code, ErrorCode.LLM_SERVICE_ERROR)
        raise ApiError(code=code, message=exc.message, status_code=exc.status_code) from exc


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _parse_sse_event(chunk: str) -> tuple[str, dict[str, Any]] | None:
    event_name = ""
    json_payload = ""

    for raw_line in chunk.splitlines():
        line = raw_line.strip()
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            json_payload = line[len("data:") :].strip()

    if not event_name or not json_payload:
        return None

    return event_name, json.loads(json_payload)


async def _persist_assistant_reply(user_id: str, conversation_id: str, assistant_chunks: list[str]) -> dict | None:
    assistant_content = "".join(assistant_chunks).strip()
    if assistant_content:
        try:
            await conversation_service.save_message(user_id, conversation_id, "assistant", assistant_content)
        except ValueError:
            pass

    return await conversation_service.get_conversation_summary(user_id, conversation_id)


async def _stream_and_persist(user_id: str, payload: ChatRequest, conversation: dict) -> AsyncIterator[str]:
    assistant_chunks: list[str] = []
    conversation_id = conversation["id"]
    user_messages = [message for message in payload.messages if message.role == "user"]

    if user_messages:
        last_user_message = user_messages[-1]
        await conversation_service.save_message(user_id, conversation_id, "user", last_user_message.content)
        conversation = await conversation_service.auto_title_from_message(user_id, conversation_id, last_user_message.content) or conversation

    yield _format_sse(
        "meta",
        {
            "mode": "stream",
            "provider": "deepseek",
            "model": llm_service.settings.openai_model,
            "conversation": conversation,
        },
    )

    try:
        async for chunk in llm_service.stream_reply(payload):
            parsed_event = _parse_sse_event(chunk)
            if parsed_event is None:
                continue

            event_name, data = parsed_event

            if event_name == "meta":
                continue

            if event_name == "message":
                delta = data.get("delta")
                if isinstance(delta, str):
                    assistant_chunks.append(delta)
                yield chunk
                continue

            if event_name == "done":
                updated_conversation = await _persist_assistant_reply(user_id, conversation_id, assistant_chunks)
                if updated_conversation:
                    data["conversation"] = updated_conversation
                yield _format_sse("done", data)
                return

            yield chunk
    except asyncio.CancelledError:
        await _persist_assistant_reply(user_id, conversation_id, assistant_chunks)
        raise
    except Exception:
        yield _format_sse(
            "error",
            {"message": "流式生成过程中发生未预期错误。", "status_code": 502},
        )
        updated_conversation = await _persist_assistant_reply(user_id, conversation_id, assistant_chunks)
        yield _format_sse(
            "done",
            {
                "finish_reason": "error",
                "conversation": updated_conversation,
            },
        )


@router.post("/stream")
async def stream_chat_reply(request: Request, payload: ChatRequest, x_user_id: str = Header()) -> StreamingResponse:
    user_id = _get_user_id(x_user_id)
    print(
        ">>> [DEBUG] /chat/stream 被访问了",
        {
            "x-agent-debug": request.headers.get("x-agent-debug"),
            "message_count": len(payload.messages),
            "conversation_id": payload.conversation_id,
            "last_message": payload.messages[-1].content if payload.messages else "无",
        },
    )
    try:
        llm_service.ensure_configured()
        llm_service.validate_request(payload)
    except LLMServiceError as exc:
        code = HTTP_STATUS_TO_CODE.get(exc.status_code, ErrorCode.LLM_SERVICE_ERROR)
        raise ApiError(code=code, message=exc.message, status_code=exc.status_code) from exc

    try:
        conversation = await conversation_service.ensure_conversation(user_id, payload.conversation_id)
    except ValueError as exc:
        raise ApiError(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=404
        ) from exc

    payload.conversation_id = conversation["id"]

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Conversation-Id": conversation["id"],
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        _stream_and_persist(user_id, payload, conversation),
        media_type="text/event-stream",
        headers=headers,
    )
