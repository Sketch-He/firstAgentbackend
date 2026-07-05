"""测试配置和共享 fixtures。"""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db, init_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """创建全局事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """每个测试前初始化数据库，测试后清理。"""
    await init_db()
    yield
    # 测试后不需要特殊清理，因为用的是内存或临时文件


@pytest_asyncio.fixture
async def client():
    """异步 HTTP 测试客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def test_user_id():
    """测试用户 ID。"""
    return "test-user-001"


@pytest.fixture
def sample_txt_file():
    """创建示例 TXT 文件。"""
    content = "这是一个测试文档。\n\n第一段内容。\n\n第二段内容。"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def sample_md_file():
    """创建示例 Markdown 文件。"""
    content = "# 测试标题\n\n这是测试内容。\n\n## 第二节\n\n更多内容。"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        return Path(f.name)
