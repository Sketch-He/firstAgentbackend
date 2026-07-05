"""文档解析服务：将上传文件解析为纯文本并分块。"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.database import get_db

# 支持的文件类型与对应扩展名。
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_file_type(filename: str) -> str | None:
    """根据扩展名检测文件类型，不支持则返回 None。"""
    ext = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext)


def parse_file(file_path: str, file_type: str) -> str:
    """解析文件为纯文本。"""
    if file_type == "pdf":
        return _parse_pdf(file_path)
    if file_type == "docx":
        return _parse_docx(file_path)
    if file_type in ("txt", "md"):
        return _parse_text(file_path)

    raise ValueError(f"不支持的文件类型：{file_type}")


def split_text(text: str) -> list[str]:
    """使用递归分割策略将文本切分为块。"""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
    )
    chunks = splitter.split_text(text)
    # 过滤掉空白块
    return [chunk for chunk in chunks if chunk.strip()]


def _parse_pdf(file_path: str) -> str:
    from pypdf2 import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _parse_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _parse_text(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


async def create_document_record(
    user_id: str,
    filename: str,
    file_type: str,
    file_size: int,
) -> dict:
    """在数据库中创建文档记录（status=processing）。"""
    doc_id = str(uuid.uuid4())
    now = _utc_now()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO documents (id, user_id, filename, file_type, file_size, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'processing', ?, ?)",
            (doc_id, user_id, filename, file_type, file_size, now, now),
        )
        await db.commit()
        return {
            "id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "chunk_count": 0,
            "status": "processing",
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        await db.close()


async def update_document_status(
    doc_id: str,
    status: str,
    chunk_count: int = 0,
    error_message: str | None = None,
) -> None:
    """更新文档状态。"""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE documents SET status = ?, chunk_count = ?, error_message = ?, updated_at = ? WHERE id = ?",
            (status, chunk_count, error_message, _utc_now(), doc_id),
        )
        await db.commit()
    finally:
        await db.close()


async def list_documents(user_id: str) -> list[dict]:
    """列出用户的所有文档。"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, filename, file_type, file_size, chunk_count, status, error_message, created_at, updated_at "
            "FROM documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_document(user_id: str, doc_id: str) -> dict | None:
    """获取单个文档详情。"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, filename, file_type, file_size, chunk_count, status, error_message, created_at, updated_at "
            "FROM documents WHERE id = ? AND user_id = ?",
            (doc_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def delete_document_record(user_id: str, doc_id: str) -> bool:
    """删除文档记录。"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?",
            (doc_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
