from fastapi import APIRouter

from app.core.exceptions import ApiError
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
    MessageOut,
    MessageSave,
)
from app.schemas.response import ApiResponse, ErrorCode
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])
conversation_service = ConversationService()


@router.get("")
async def list_conversations() -> ApiResponse[list[ConversationSummary]]:
    data = await conversation_service.list_conversations()
    return ApiResponse.success(data=data)


@router.post("", status_code=201)
async def create_conversation(body: ConversationCreate) -> ApiResponse[ConversationSummary]:
    data = await conversation_service.create_conversation(title=body.title)
    return ApiResponse.success(data=data, message="会话创建成功。")


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str) -> ApiResponse[ConversationDetail]:
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise ApiError(code=ErrorCode.NOT_FOUND, message="会话不存在。", status_code=404)
    return ApiResponse.success(data=conversation)


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str, body: ConversationUpdate
) -> ApiResponse[ConversationSummary]:
    conversation = await conversation_service.update_title(conversation_id, body.title)
    if not conversation:
        raise ApiError(code=ErrorCode.NOT_FOUND, message="会话不存在。", status_code=404)
    return ApiResponse.success(data=conversation, message="标题更新成功。")


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str) -> ApiResponse:
    deleted = await conversation_service.delete_conversation(conversation_id)
    if not deleted:
        raise ApiError(code=ErrorCode.NOT_FOUND, message="会话不存在。", status_code=404)
    return ApiResponse.success(message="会话已删除。")


@router.delete("/{conversation_id}/last-turn")
async def delete_last_turn(conversation_id: str) -> ApiResponse[ConversationSummary]:
    conversation = await conversation_service.get_conversation_summary(conversation_id)
    if not conversation:
        raise ApiError(code=ErrorCode.NOT_FOUND, message="会话不存在。", status_code=404)

    updated = await conversation_service.delete_last_turn(conversation_id)
    if not updated:
        raise ApiError(
            code=ErrorCode.CONFLICT,
            message="当前会话没有可重试的上一轮消息。",
            status_code=409,
        )

    return ApiResponse.success(data=updated, message="上一轮已删除，可以重试。")


@router.post("/{conversation_id}/messages", status_code=201)
async def save_message(conversation_id: str, body: MessageSave) -> ApiResponse[MessageOut]:
    conversation = await conversation_service.get_conversation_summary(conversation_id)
    if not conversation:
        raise ApiError(code=ErrorCode.NOT_FOUND, message="会话不存在。", status_code=404)
    try:
        data = await conversation_service.save_message(
            conversation_id, body.role, body.content
        )
    except ValueError as exc:
        raise ApiError(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=400
        ) from exc
    return ApiResponse.success(data=data, message="消息保存成功。")
