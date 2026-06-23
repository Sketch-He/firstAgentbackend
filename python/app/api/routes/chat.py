from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LLMService, LLMServiceError

router = APIRouter(prefix="/chat", tags=["chat"])
llm_service = LLMService()


@router.post("", response_model=ChatResponse)
async def create_chat_reply(request: ChatRequest) -> ChatResponse:
    # 这个接口用于普通一次性返回。
    try:
        return await llm_service.generate_reply(request)
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/stream")
async def stream_chat_reply(request: Request, payload: ChatRequest) -> StreamingResponse:
    print(
        ">>> [DEBUG] /chat/stream 被访问了",
        {
            "x-agent-debug": request.headers.get("x-agent-debug"),
            "message_count": len(payload.messages),
            "last_message": payload.messages[-1].content if payload.messages else "无"
        }
    )
    try:
        llm_service.ensure_configured()
        llm_service.validate_request(payload)
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    # 这个接口用于前端 SSE 流式输出。
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }

    return StreamingResponse(
        llm_service.stream_reply(payload),
        media_type="text/event-stream",
        headers=headers
    )
