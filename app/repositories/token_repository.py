from __future__ import annotations

from typing import Optional

from app.db import Database
from app.utils.time_utils import compute_expires_at


class TokenRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_partner_token(
        self,
        client_id: str,
        access_token: str,
        token_type: Optional[str],
        expires_in: Optional[int],
        scope: Optional[str],
        audience: Optional[str],
    ) -> None:
        expires_at = compute_expires_at(expires_in)
        self.db.execute(
            "UPDATE tesla_partner_token SET is_latest = 0 WHERE client_id = %s AND is_latest = 1",
            (client_id,),
        )
        self.db.execute(
            """
            INSERT INTO tesla_partner_token
            (client_id, access_token, token_type, expires_in, expires_at, scope, audience, is_latest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (client_id, access_token, token_type, expires_in, expires_at, scope, audience),
        )

    def latest_partner_token(self, client_id: str) -> Optional[dict]:
        return self.db.fetchone(
            """
            SELECT * FROM tesla_partner_token
            WHERE client_id = %s AND is_latest = 1
            ORDER BY id DESC LIMIT 1
            """,
            (client_id,),
        )

    def save_third_party_token(
        self,
        user_id: int,
        client_id: str,
        access_token: str,
        refresh_token: Optional[str],
        id_token: Optional[str],
        token_type: Optional[str],
        expires_in: Optional[int],
        scope: Optional[str],
        audience: Optional[str],
        oauth_state: Optional[str],
        tesla_user_sub: Optional[str] = None,
    ) -> None:
        expires_at = compute_expires_at(expires_in)
        self.db.execute(
            "UPDATE tesla_third_party_token SET is_latest = 0 WHERE user_id = %s AND is_latest = 1",
            (user_id,),
        )
        self.db.execute(
            """
            INSERT INTO tesla_third_party_token
            (user_id, client_id, tesla_user_sub, access_token, refresh_token, id_token, token_type,
             expires_in, access_token_expires_at, scope, audience, oauth_state, is_latest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (
                user_id,
                client_id,
                tesla_user_sub,
                access_token,
                refresh_token,
                id_token,
                token_type,
                expires_in,
                expires_at,
                scope,
                audience,
                oauth_state,
            ),
        )

    def latest_third_party_token(self, user_id: int) -> Optional[dict]:
        return self.db.fetchone(
            """
            SELECT * FROM tesla_third_party_token
            WHERE user_id = %s AND is_latest = 1
            ORDER BY id DESC LIMIT 1
            """,
            (user_id,),
        )
