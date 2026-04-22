from __future__ import annotations

from typing import Optional

from app.db import Database


class PartnerRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_by_domain(self, domain: str) -> Optional[dict]:
        return self.db.fetchone(
            "SELECT * FROM tesla_partner_account WHERE domain = %s LIMIT 1",
            (domain,),
        )

    def save_account(
        self,
        domain: str,
        account_id: Optional[str],
        name: Optional[str],
        description: Optional[str],
        public_key_hex: Optional[str] = None,
    ) -> None:
        existing = self.get_by_domain(domain)
        public_key_pem_url = f"https://{domain}/.well-known/appspecific/com.tesla.3p.public-key.pem"

        if existing:
            self.db.execute(
                """
                UPDATE tesla_partner_account
                SET account_id = COALESCE(%s, account_id),
                    name = COALESCE(%s, name),
                    description = COALESCE(%s, description),
                    public_key_hex = COALESCE(%s, public_key_hex),
                    public_key_pem_url = %s,
                    is_active = 1,
                    updated_at = NOW()
                WHERE domain = %s
                """,
                (account_id, name, description, public_key_hex, public_key_pem_url, domain),
            )
            return

        if not account_id:
            raise ValueError(
                f"domain={domain} not found locally and account_id is missing. "
                f"Register partner account first."
            )

        self.db.execute(
            """
            INSERT INTO tesla_partner_account
            (domain, account_id, name, description, public_key_hex, public_key_pem_url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            (domain, account_id, name, description, public_key_hex, public_key_pem_url),
        )
