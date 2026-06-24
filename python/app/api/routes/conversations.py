from fastapi import APIRouter, HTTPException

from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
    MessageOut,
    MessageSave,
)
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])
conversation_service = ConversationService()


@router.get("", response_model=list[ConversationSummary])
async def list_conversations() -> list[dict]:
    return await conversation_service.list_conversations()


@router.post("", response_model=ConversationSummary, status_code=201)
async def create_conversation(body: ConversationCreate) -> dict:
    return await conversation_service.create_conversation(title=body.title)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str) -> dict:
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(conversation_id: str, body: ConversationUpdate) -> dict:
    conversation = await conversation_service.update_title(conversation_id, body.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str) -> None:
    deleted = await conversation_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在。")


@router.delete("/{conversation_id}/last-turn", response_model=ConversationSummary)
async def delete_last_turn(conversation_id: str) -> dict:
    conversation = await conversation_service.get_conversation_summary(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在。")

    updated = await conversation_service.delete_last_turn(conversation_id)
    if not updated:
        raise HTTPException(status_code=409, detail="当前会话没有可重试的上一轮消息。")

    return updated


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def save_message(conversation_id: str, body: MessageSave) -> dict:
    conversation = await conversation_service.get_conversation_summary(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在。")
    try:
        return await conversation_service.save_message(conversation_id, body.role, body.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
