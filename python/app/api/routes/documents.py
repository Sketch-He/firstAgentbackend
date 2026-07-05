"""文档管理 API 路由。"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Header, UploadFile

from app.core.config import get_settings
from app.core.exceptions import ApiError
from app.schemas.document import DocumentListResponse, DocumentOut
from app.schemas.response import ApiResponse, ErrorCode
from app.services.document import (
    create_document_record,
    delete_document_record,
    detect_file_type,
    get_document,
    list_documents,
    parse_file,
    split_text,
    update_document_status,
)
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/documents", tags=["documents"])
vector_store = VectorStoreService()

# 上传文件存储目录（持久化，支持重试）
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
}


def _get_user_id(x_user_id: str = Header(default="")) -> str:
    if not x_user_id:
        raise ApiError(code=ErrorCode.BAD_REQUEST, message="缺少 X-User-Id 请求头。", status_code=400)
    return x_user_id


def _get_upload_path(doc_id: str, filename: str) -> Path:
    """获取上传文件的持久化存储路径。"""
    suffix = Path(filename).suffix
    return UPLOADS_DIR / f"{doc_id}{suffix}"


async def _process_document_background(
    doc_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    filename: str,
) -> None:
    """后台任务：解析文档 → 分块 → 向量化 → 存储。"""
    try:
        # 解析文件为纯文本
        text = await asyncio.to_thread(parse_file, file_path, file_type)
        if not text.strip():
            await update_document_status(doc_id, "failed", error_message="文档内容为空。")
            return

        # 分块
        chunks = await asyncio.to_thread(split_text, text)
        if not chunks:
            await update_document_status(doc_id, "failed", error_message="文档分块后无有效内容。")
            return

        # 向量化并存储
        await vector_store.add_document(user_id, doc_id, filename, chunks)

        # 更新状态
        await update_document_status(doc_id, "ready", chunk_count=len(chunks))
    except Exception as exc:
        error_msg = f"文档处理失败：{exc!s}"
        await update_document_status(doc_id, "failed", error_message=error_msg)
    # 注意：不再删除上传的文件，保留以便重试


@router.post("/upload")
async def upload_document(
    file: UploadFile,
    x_user_id: str = Header(),
) -> ApiResponse[DocumentOut]:
    """上传文档，后台异步处理。"""
    user_id = _get_user_id(x_user_id)
    settings = get_settings()

    # 校验文件名
    if not file.filename:
        raise ApiError(code=ErrorCode.BAD_REQUEST, message="文件名不能为空。", status_code=400)

    # 校验文件类型
    file_type = detect_file_type(file.filename)
    if file_type is None:
        supported = ", ".join(sorted(set(SUPPORTED_EXTENSIONS.values())))
        raise ApiError(
            code=ErrorCode.UNSUPPORTED_FILE_TYPE,
            message=f"不支持的文件格式。支持的格式：{supported}",
            status_code=400,
        )

    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 校验文件大小
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise ApiError(
            code=ErrorCode.DOCUMENT_TOO_LARGE,
            message=f"文件大小超过限制（最大 {settings.max_upload_size_mb}MB）。",
            status_code=400,
        )

    # 创建数据库记录
    doc = await create_document_record(user_id, file.filename, file_type, file_size)

    # 保存文件到持久化目录（支持重试）
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_path = _get_upload_path(doc["id"], file.filename)
    upload_path.write_bytes(content)

    # 启动后台任务处理文档
    asyncio.create_task(
        _process_document_background(doc["id"], user_id, str(upload_path), file_type, file.filename)
    )

    return ApiResponse.success(data=doc, message="文档已上传，正在后台处理。")


@router.get("")
async def list_user_documents(x_user_id: str = Header()) -> ApiResponse[DocumentListResponse]:
    """列出当前用户的所有文档。"""
    user_id = _get_user_id(x_user_id)
    docs = await list_documents(user_id)
    return ApiResponse.success(data=DocumentListResponse(documents=docs))


@router.get("/{doc_id}")
async def get_document_detail(doc_id: str, x_user_id: str = Header()) -> ApiResponse[DocumentOut]:
    """获取文档详情（可用于轮询状态）。"""
    user_id = _get_user_id(x_user_id)
    doc = await get_document(user_id, doc_id)
    if not doc:
        raise ApiError(code=ErrorCode.DOCUMENT_NOT_FOUND, message="文档不存在。", status_code=404)
    return ApiResponse.success(data=doc)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, x_user_id: str = Header()) -> ApiResponse:
    """删除文档、向量数据和上传文件。"""
    user_id = _get_user_id(x_user_id)
    doc = await get_document(user_id, doc_id)
    if not doc:
        raise ApiError(code=ErrorCode.DOCUMENT_NOT_FOUND, message="文档不存在。", status_code=404)

    # 删除向量数据
    try:
        vector_store.delete_document(user_id, doc_id)
    except Exception:
        pass

    # 删除上传文件
    upload_path = _get_upload_path(doc_id, doc["filename"])
    try:
        upload_path.unlink(missing_ok=True)
    except OSError:
        pass

    # 删除数据库记录
    await delete_document_record(user_id, doc_id)
    return ApiResponse.success(message="文档已删除。")


@router.post("/{doc_id}/retry")
async def retry_document(doc_id: str, x_user_id: str = Header()) -> ApiResponse[DocumentOut]:
    """重新处理失败的文档。"""
    user_id = _get_user_id(x_user_id)
    doc = await get_document(user_id, doc_id)
    if not doc:
        raise ApiError(code=ErrorCode.DOCUMENT_NOT_FOUND, message="文档不存在。", status_code=404)

    if doc["status"] != "failed":
        raise ApiError(
            code=ErrorCode.CONFLICT,
            message="只能重试处理失败的文档。",
            status_code=409,
        )

    # 检查上传文件是否存在
    upload_path = _get_upload_path(doc_id, doc["filename"])
    if not upload_path.exists():
        raise ApiError(
            code=ErrorCode.CONFLICT,
            message="原始文件已丢失，请重新上传。",
            status_code=409,
        )

    # 重置状态并重新处理
    await update_document_status(doc_id, "processing")
    doc["status"] = "processing"
    doc["error_message"] = None

    file_type = detect_file_type(doc["filename"])
    asyncio.create_task(
        _process_document_background(doc_id, user_id, str(upload_path), file_type or "txt", doc["filename"])
    )

    return ApiResponse.success(data=doc, message="文档已重新提交处理。")
