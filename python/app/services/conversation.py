import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.schemas.chat import ChatRole

DEFAULT_CONVERSATION_TITLE = "新对话"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_title(title: str) -> str:
    normalized = title.strip()
    return normalized or DEFAULT_CONVERSATION_TITLE


class ConversationService:
    async def list_conversations(self, user_id: str) -> list[dict]:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def create_conversation(self, user_id: str, title: str = DEFAULT_CONVERSATION_TITLE) -> dict:
        conversation_id = str(uuid.uuid4())
        now = _utc_now()
        normalized_title = _normalize_title(title)
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, user_id, normalized_title, now, now),
            )
            await db.commit()
            return {
                "id": conversation_id,
                "title": normalized_title,
                "created_at": now,
                "updated_at": now,
            }
        finally:
            await db.close()

    async def ensure_conversation(self, user_id: str, conversation_id: str | None) -> dict:
        if conversation_id:
            conversation = await self.get_conversation_summary(user_id, conversation_id)
            if conversation is None:
                raise ValueError("会话不存在。")
            return conversation

        return await self.create_conversation(user_id)

    async def get_conversation_summary(self, user_id: str, conversation_id: str) -> dict | None:
        db = await get_db()
        try:
            return await self._get_conversation_summary_with_db(db, user_id, conversation_id)
        finally:
            await db.close()

    async def get_conversation(self, user_id: str, conversation_id: str) -> dict | None:
        db = await get_db()
        try:
            conversation = await self._get_conversation_summary_with_db(db, user_id, conversation_id)
            if not conversation:
                return None

            cursor = await db.execute(
                "SELECT id, role, content, sort_order, created_at FROM messages WHERE conversation_id = ? ORDER BY sort_order",
                (conversation_id,),
            )
            messages = [dict(r) for r in await cursor.fetchall()]
            conversation["messages"] = messages
            return conversation
        finally:
            await db.close()

    async def update_title(self, user_id: str, conversation_id: str, title: str) -> dict | None:
        db = await get_db()
        try:
            cursor = await db.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (_normalize_title(title), _utc_now(), conversation_id, user_id),
            )
            if cursor.rowcount <= 0:
                await db.rollback()
                return None
            await db.commit()
            return await self._get_conversation_summary_with_db(db, user_id, conversation_id)
        finally:
            await db.close()

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        db = await get_db()
        try:
            cursor = await db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def save_message(self, user_id: str, conversation_id: str, role: ChatRole, content: str) -> dict:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("消息内容不能为空。")

        now = _utc_now()
        message_id = str(uuid.uuid4())
        db = await get_db()
        try:
            await db.execute("BEGIN IMMEDIATE")
            conversation = await self._get_conversation_summary_with_db(db, user_id, conversation_id)
            if conversation is None:
                await db.rollback()
                raise ValueError("会话不存在。")

            cursor = await db.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            sort_order = (await cursor.fetchone())[0]

            await db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, sort_order, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, normalized_content, sort_order, now),
            )
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            await db.commit()
            return {
                "id": message_id,
                "role": role,
                "content": normalized_content,
                "sort_order": sort_order,
                "created_at": now,
            }
        finally:
            await db.close()

    async def auto_title_from_message(self, user_id: str, conversation_id: str, content: str) -> dict | None:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT title FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            if row["title"] == DEFAULT_CONVERSATION_TITLE:
                normalized_content = content.strip()
                title = normalized_content[:20]
                if len(normalized_content) > 20:
                    title += "..."
                await db.execute(
                    "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                    (_normalize_title(title), _utc_now(), conversation_id),
                )
                await db.commit()

            return await self._get_conversation_summary_with_db(db, user_id, conversation_id)
        finally:
            await db.close()

    async def delete_last_turn(self, user_id: str, conversation_id: str) -> dict | None:
        db = await get_db()
        try:
            await db.execute("BEGIN IMMEDIATE")
            conversation = await self._get_conversation_summary_with_db(db, user_id, conversation_id)
            if conversation is None:
                await db.rollback()
                return None

            cursor = await db.execute(
                "SELECT sort_order, role FROM messages WHERE conversation_id = ? ORDER BY sort_order DESC",
                (conversation_id,),
            )
            rows = await cursor.fetchall()

            last_user_sort_order = next(
                (row["sort_order"] for row in rows if row["role"] == "user"),
                None,
            )
            if last_user_sort_order is None:
                await db.rollback()
                return None

            await db.execute(
                "DELETE FROM messages WHERE conversation_id = ? AND sort_order >= ?",
                (conversation_id, last_user_sort_order),
            )

            cursor = await db.execute(
                "SELECT COUNT(*) AS message_count FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            message_count = (await cursor.fetchone())["message_count"]
            next_title = conversation["title"] if message_count > 0 else DEFAULT_CONVERSATION_TITLE
            await db.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (next_title, _utc_now(), conversation_id),
            )
            await db.commit()
            return await self._get_conversation_summary_with_db(db, user_id, conversation_id)
        finally:
            await db.close()

    async def _get_conversation_summary_with_db(self, db, user_id: str, conversation_id: str) -> dict | None:
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
