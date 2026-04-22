from __future__ import annotations

from datetime import timedelta
from typing import Optional

from config import (
    DEFAULT_SCOPES,
    TESLA_AUDIENCE,
    TESLA_CLIENT_ID,
    TESLA_PARTNER_DOMAIN,
    TOKEN_REFRESH_BEFORE_MINUTES,
)
from app.db import Database
from app.exceptions import TeslaOAuthError, TeslaPartnerAccountError
from app.repositories.oauth_repository import OAuthRepository
from app.repositories.partner_repository import PartnerRepository
from app.repositories.token_repository import TokenRepository
from app.tesla.cn_auth_api import TeslaCnAuthApi
from app.tesla.partner_api import PartnerApi
from app.utils.time_utils import now, to_datetime


class AuthService:
    def __init__(self):
        db = Database()
        self.auth_api = TeslaCnAuthApi()
        self.partner_api = PartnerApi()
        self.partner_repo = PartnerRepository(db)
        self.token_repo = TokenRepository(db)
        self.oauth_repo = OAuthRepository(db)
        self.client_id = TESLA_CLIENT_ID
        self.partner_domain = TESLA_PARTNER_DOMAIN

    def build_authorize_url(self, user_id: int, scopes: Optional[list[str]] = None) -> dict:
        data = self.auth_api.build_authorize_url(scopes=scopes or list(DEFAULT_SCOPES))
        self.oauth_repo.create_session(
            user_id=user_id,
            state=data["state"],
            nonce=data["nonce"],
            redirect_uri=self.auth_api.redirect_uri,
            scopes=data["scopes"],
            authorize_url=data["authorize_url"],
        )
        return data

    def get_partner_token(self, scope: Optional[str] = None) -> dict:
        data = self.auth_api.get_partner_token(scope=scope)
        self.token_repo.save_partner_token(
            client_id=self.client_id,
            access_token=data["access_token"],
            token_type=data.get("token_type"),
            expires_in=data.get("expires_in"),
            scope=scope or "openid vehicle_device_data vehicle_cmds vehicle_charging_cmds",
            audience=TESLA_AUDIENCE,
        )
        return data

    def ensure_partner_token(self) -> str:
        latest = self.token_repo.latest_partner_token(self.client_id)
        if latest:
            expires_at = to_datetime(latest.get("expires_at"))
            if expires_at and expires_at > now() + timedelta(minutes=TOKEN_REFRESH_BEFORE_MINUTES):
                return latest["access_token"]
        return self.get_partner_token()["access_token"]

    def register_partner_account(self, domain: Optional[str] = None) -> dict:
        domain = domain or self.partner_domain
        access_token = self.ensure_partner_token()
        result = self.partner_api.register_partner_account(domain=domain, access_token=access_token)
        response_data = result.get("response") or {}
        self.partner_repo.save_account(
            domain=domain,
            account_id=response_data.get("account_id"),
            name=response_data.get("name"),
            description=response_data.get("description"),
        )
        return result

    def sync_partner_public_key(self, domain: Optional[str] = None) -> dict:
        domain = domain or self.partner_domain
        local = self.partner_repo.get_by_domain(domain)
        if not local:
            raise TeslaPartnerAccountError(
                f"Partner account for domain={domain} is not stored locally yet. Register it first."
            )
        access_token = self.ensure_partner_token()
        result = self.partner_api.get_public_key(domain=domain, access_token=access_token)
        public_key_hex = (result.get("response") or {}).get("public_key")
        self.partner_repo.save_account(
            domain=domain,
            account_id=None,
            name=None,
            description=None,
            public_key_hex=public_key_hex,
        )
        return result

    def initialize_partner(self, domain: Optional[str] = None) -> dict:
        domain = domain or self.partner_domain
        register_result: dict
        try:
            register_result = self.register_partner_account(domain=domain)
        except TeslaPartnerAccountError as exc:
            message = str(exc).lower()
            if "already" in message or "exists" in message or "409" in message:
                local_account = self.partner_repo.get_by_domain(domain)
                if not local_account:
                    raise
                register_result = {
                    "status": "already_exists",
                    "message": str(exc),
                    "local_account": local_account,
                }
            else:
                raise
        public_key_result = self.sync_partner_public_key(domain=domain)
        local_account = self.partner_repo.get_by_domain(domain)
        return {
            "domain": domain,
            "partner_account": register_result,
            "public_key": public_key_result,
            "local_account": local_account,
        }

    def exchange_code_for_token(self, code: str, state: str) -> dict:
        oauth_session = self.oauth_repo.get_by_state(state)
        if not oauth_session:
            raise TeslaOAuthError("Unknown state; no OAuth session found.")
        user_id = oauth_session["user_id"]
        data = self.auth_api.exchange_code(code=code)
        self.oauth_repo.mark_callback_success(state=state, code=code)
        self.token_repo.save_third_party_token(
            user_id=user_id,
            client_id=self.client_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            token_type=data.get("token_type"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
            audience=TESLA_AUDIENCE,
            oauth_state=state,
        )
        self.oauth_repo.mark_exchanged(state)
        return data

    def mark_oauth_failure(self, state: str, error_message: str) -> None:
        self.oauth_repo.mark_callback_failed(state, error_message)

    def latest_third_party_token(self, user_id: int) -> Optional[dict]:
        return self.token_repo.latest_third_party_token(user_id)

    def ensure_third_party_token(self, user_id: int) -> str:
        latest = self.latest_third_party_token(user_id)
        if not latest:
            raise TeslaOAuthError("No third-party token found. Complete OAuth first.")
        expires_at = to_datetime(latest.get("access_token_expires_at"))
        if expires_at and expires_at > now() + timedelta(minutes=TOKEN_REFRESH_BEFORE_MINUTES):
            return latest["access_token"]
        refresh_token = latest.get("refresh_token")
        if not refresh_token:
            raise TeslaOAuthError("No refresh token found. Re-authorize required.")
        data = self.auth_api.refresh_token(refresh_token=refresh_token)
        self.token_repo.save_third_party_token(
            user_id=user_id,
            client_id=self.client_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            token_type=data.get("token_type"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
            audience=TESLA_AUDIENCE,
            oauth_state=None,
        )
        return data["access_token"]
