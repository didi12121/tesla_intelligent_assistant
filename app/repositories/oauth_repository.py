from __future__ import annotations

from typing import Optional

from app.db import Database


class OAuthRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_session(
        self,
        user_id: int,
        state: str,
        nonce: str,
        redirect_uri: str,
        scopes: str,
        authorize_url: str,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO tesla_oauth_session
            (user_id, state, nonce, redirect_uri, scopes, authorize_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'CREATED')
            """,
            (user_id, state, nonce, redirect_uri, scopes, authorize_url),
        )

    def get_by_state(self, state: str) -> Optional[dict]:
        return self.db.fetchone(
            "SELECT * FROM tesla_oauth_session WHERE state = %s LIMIT 1",
            (state,),
        )

    def mark_callback_success(self, state: str, code: str) -> None:
        self.db.execute(
            """
            UPDATE tesla_oauth_session
            SET status = 'CALLBACK_SUCCESS', code = %s, updated_at = NOW()
            WHERE state = %s
            """,
            (code, state),
        )

    def mark_callback_failed(self, state: str, error_message: str) -> None:
        self.db.execute(
            """
            UPDATE tesla_oauth_session
            SET status = 'CALLBACK_FAILED', error_message = %s, updated_at = NOW()
            WHERE state = %s
            """,
            (error_message, state),
        )

    def mark_exchanged(self, state: str) -> None:
        self.db.execute(
            """
            UPDATE tesla_oauth_session
            SET status = 'EXCHANGED', updated_at = NOW()
            WHERE state = %s
            """,
            (state,),
        )
