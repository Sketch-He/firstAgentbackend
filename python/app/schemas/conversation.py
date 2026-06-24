from pydantic import BaseModel, Field

from app.schemas.chat import ChatRole


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", min_length=1)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1)


class MessageSave(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sort_order: int
    created_at: str


class ConversationDetail(ConversationSummary):
    messages: list[MessageOut] = Field(default_factory=list)
