"""文档 API 测试。"""

import pytest
from httpx import AsyncClient

from app.services.document import create_document_record, delete_document_record


class TestDocumentsAPI:
    """文档管理 API 测试。"""

    @pytest.mark.asyncio
    async def test_upload_document(self, client: AsyncClient, test_user_id):
        """测试上传文档。"""
        files = {"file": ("test.txt", b"Hello World", "text/plain")}
        headers = {"X-User-Id": test_user_id}

        response = await client.post("/api/documents/upload", files=files, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["filename"] == "test.txt"
        assert data["data"]["status"] == "processing"

        # 清理
        await delete_document_record(test_user_id, data["data"]["id"])

    @pytest.mark.asyncio
    async def test_upload_without_user_id(self, client: AsyncClient):
        """测试没有 user_id 时上传失败（FastAPI 参数校验返回 422）。"""
        files = {"file": ("test.txt", b"Hello World", "text/plain")}
        response = await client.post("/api/documents/upload", files=files)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_unsupported_type(self, client: AsyncClient, test_user_id):
        """测试上传不支持的文件类型（返回 400）。"""
        files = {"file": ("test.xlsx", b"content", "application/vnd.ms-excel")}
        headers = {"X-User-Id": test_user_id}

        response = await client.post("/api/documents/upload", files=files, headers=headers)
        assert response.status_code == 400

        data = response.json()
        assert data["code"] != 0

    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient, test_user_id):
        """测试列出文档。"""
        headers = {"X-User-Id": test_user_id}

        response = await client.get("/api/documents", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "documents" in data["data"]

    @pytest.mark.asyncio
    async def test_get_document(self, client: AsyncClient, test_user_id):
        """测试获取文档详情。"""
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)

        headers = {"X-User-Id": test_user_id}
        response = await client.get(f"/api/documents/{doc['id']}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == doc["id"]

        await delete_document_record(test_user_id, doc["id"])

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client: AsyncClient, test_user_id):
        """测试获取不存在的文档（返回 404）。"""
        headers = {"X-User-Id": test_user_id}
        response = await client.get("/api/documents/nonexistent-id", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document(self, client: AsyncClient, test_user_id):
        """测试删除文档。"""
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)

        headers = {"X-User-Id": test_user_id}
        response = await client.delete(f"/api/documents/{doc['id']}", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

        # 确认已删除
        response = await client.get(f"/api/documents/{doc['id']}", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_document_without_file(self, client: AsyncClient, test_user_id):
        """测试重试失败的文档但文件不存在（返回 409）。"""
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)
        from app.services.document import update_document_status
        await update_document_status(doc["id"], "failed", error_message="测试错误")

        headers = {"X-User-Id": test_user_id}
        response = await client.post(f"/api/documents/{doc['id']}/retry", headers=headers)
        # 文件不存在，应该返回 409
        assert response.status_code == 409

        await delete_document_record(test_user_id, doc["id"])

    @pytest.mark.asyncio
    async def test_retry_non_failed_document(self, client: AsyncClient, test_user_id):
        """测试重试非失败状态的文档（返回 409）。"""
        doc = await create_document_record(test_user_id, "test.txt", "txt", 100)

        headers = {"X-User-Id": test_user_id}
        response = await client.post(f"/api/documents/{doc['id']}/retry", headers=headers)
        # 不是 failed 状态，应该返回 409
        assert response.status_code == 409

        await delete_document_record(test_user_id, doc["id"])
