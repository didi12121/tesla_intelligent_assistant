from __future__ import annotations

from typing import Optional

from app.db import Database


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_by_username(self, username: str) -> Optional[dict]:
        return self.db.fetchone(
            "SELECT * FROM tesla_app_user WHERE username = %s AND is_active = 1 LIMIT 1",
            (username,),
        )

    def create(self, username: str, password_hash: str) -> int:
        return self.db.execute(
            "INSERT INTO tesla_app_user (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )

    def username_exists(self, username: str) -> bool:
        row = self.db.fetchone(
            "SELECT id FROM tesla_app_user WHERE username = %s LIMIT 1",
            (username,),
        )
        return row is not None
