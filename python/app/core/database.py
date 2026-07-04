from pathlib import Path

import aiosqlite

from app.core.config import get_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '新对话',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    sort_order INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, sort_order);

CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_conversation_sort_order
    ON messages(conversation_id, sort_order);
"""


def get_db_path() -> Path:
    return get_settings().resolved_sqlite_path


async def get_db() -> aiosqlite.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(SCHEMA_SQL)
        # 兼容旧数据库：尝试添加 user_id 字段，已存在则忽略
        try:
            await db.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        # 确保索引存在（新旧数据库都需要）
        await db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
        await db.commit()
    finally:
        await db.close()
