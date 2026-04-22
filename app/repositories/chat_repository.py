from __future__ import annotations

from app.db import Database


class ChatRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_message(self, user_id: int, role: str, content: str) -> int:
        return self.db.execute(
            "INSERT INTO tesla_chat_message (user_id, role, content) VALUES (%s, %s, %s)",
            (user_id, role, content),
        )

    def get_recent_messages(self, user_id: int, limit: int = 20) -> list[dict]:
        return self.db.fetchall(
            """
            SELECT role, content, created_at FROM tesla_chat_message
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
