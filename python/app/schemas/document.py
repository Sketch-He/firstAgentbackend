"""文档与 RAG 相关数据模型。"""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chat import ChatMessage


class DocumentOut(BaseModel):
    """文档详情输出。"""

    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: str | None = None
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    """文档列表响应。"""

    documents: list[DocumentOut] = Field(default_factory=list)


RagMode = Literal["auto", "always", "never"]


class RagChatRequest(BaseModel):
    """RAG 聊天请求。"""

    messages: list[ChatMessage] = Field(default_factory=list)
    conversation_id: str | None = Field(default=None, min_length=1)
    rag_mode: RagMode = Field(default="auto", description="RAG 检索模式")
    top_k: int | None = Field(default=None, ge=1, le=20, description="检索片段数")


class RagSource(BaseModel):
    """RAG 检索来源。"""

    document_id: str
    filename: str
    chunk_index: int
    snippet: str
