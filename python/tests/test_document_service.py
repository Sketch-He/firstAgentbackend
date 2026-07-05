"""文档服务测试。"""

import asyncio
from pathlib import Path

import pytest

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


class TestDetectFileType:
    """文件类型检测测试。"""

    def test_pdf(self):
        assert detect_file_type("document.pdf") == "pdf"

    def test_docx(self):
        assert detect_file_type("document.docx") == "docx"

    def test_txt(self):
        assert detect_file_type("document.txt") == "txt"

    def test_md(self):
        assert detect_file_type("document.md") == "md"

    def test_uppercase(self):
        assert detect_file_type("document.PDF") == "pdf"
        assert detect_file_type("document.TXT") == "txt"

    def test_unsupported(self):
        assert detect_file_type("document.xlsx") is None
        assert detect_file_type("document.jpg") is None
        assert detect_file_type("document") is None


class TestParseFile:
    """文件解析测试。"""

    def test_parse_txt(self, sample_txt_file):
        text = parse_file(str(sample_txt_file), "txt")
        assert "测试文档" in text
        assert "第一段" in text

    def test_parse_md(self, sample_md_file):
        text = parse_file(str(sample_md_file), "md")
        assert "测试标题" in text
        assert "第二节" in text

    def test_parse_empty_file(self, tmp_path):
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        text = parse_file(str(empty_file), "txt")
        assert text == ""

    def test_parse_unsupported_type(self, sample_txt_file):
        with pytest.raises(ValueError, match="不支持的文件类型"):
            parse_file(str(sample_txt_file), "xlsx")


class TestSplitText:
    """文本分块测试。"""

    def test_split_short_text(self):
        text = "这是一段短文本。"
        chunks = split_text(text)
        assert len(chunks) >= 1
        assert chunks[0] == text

    def test_split_long_text(self):
        # 创建一个足够长的文本
        text = "这是一段测试文本。\n\n" * 100
        chunks = split_text(text)
        assert len(chunks) > 1

    def test_split_empty_text(self):
        chunks = split_text("")
        assert len(chunks) == 0

    def test_split_whitespace_only(self):
        chunks = split_text("   \n\n   ")
        assert len(chunks) == 0


class TestDocumentCRUD:
    """文档记录 CRUD 测试。"""

    @pytest.mark.asyncio
    async def test_create_and_get(self, test_user_id):
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)
        assert doc["filename"] == "test.txt"
        assert doc["status"] == "processing"
        assert doc["file_size"] == 100

        # 获取
        fetched = await get_document(test_user_id, doc["id"])
        assert fetched is not None
        assert fetched["id"] == doc["id"]

        # 清理
        await delete_document_record(test_user_id, doc["id"])

    @pytest.mark.asyncio
    async def test_list_documents(self, test_user_id):
        # 创建多个文档
        doc1 = await create_document_record(test_user_id, "a.txt", "txt", 100)
        doc2 = await create_document_record(test_user_id, "b.txt", "txt", 200)

        docs = await list_documents(test_user_id)
        assert len(docs) >= 2

        # 清理
        await delete_document_record(test_user_id, doc1["id"])
        await delete_document_record(test_user_id, doc2["id"])

    @pytest.mark.asyncio
    async def test_update_status(self, test_user_id):
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)
        assert doc["status"] == "processing"

        await update_document_status(doc["id"], "ready", chunk_count=5)
        updated = await get_document(test_user_id, doc["id"])
        assert updated["status"] == "ready"
        assert updated["chunk_count"] == 5

        # 清理
        await delete_document_record(test_user_id, doc["id"])

    @pytest.mark.asyncio
    async def test_update_status_failed(self, test_user_id):
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)

        await update_document_status(doc["id"], "failed", error_message="解析失败")
        updated = await get_document(test_user_id, doc["id"])
        assert updated["status"] == "failed"
        assert updated["error_message"] == "解析失败"

        # 清理
        await delete_document_record(test_user_id, doc["id"])

    @pytest.mark.asyncio
    async def test_delete(self, test_user_id):
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)
        deleted = await delete_document_record(test_user_id, doc["id"])
        assert deleted is True

        fetched = await get_document(test_user_id, doc["id"])
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, test_user_id):
        result = await get_document(test_user_id, "nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, test_user_id):
        result = await delete_document_record(test_user_id, "nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_user_isolation(self):
        """不同用户的数据应该隔离。"""
        user_a = "user-a"
        user_b = "user-b"

        doc_a = await create_document_record(user_a, "a.txt", "txt", 100)
        doc_b = await create_document_record(user_b, "b.txt", "txt", 200)

        # user_a 只能看到自己的文档
        docs_a = await list_documents(user_a)
        assert all(d["id"] != doc_b["id"] for d in docs_a)

        # user_b 只能看到自己的文档
        docs_b = await list_documents(user_b)
        assert all(d["id"] != doc_a["id"] for d in docs_b)

        # user_a 不能获取 user_b 的文档
        result = await get_document(user_a, doc_b["id"])
        assert result is None

        # 清理
        await delete_document_record(user_a, doc_a["id"])
        await delete_document_record(user_b, doc_b["id"])
