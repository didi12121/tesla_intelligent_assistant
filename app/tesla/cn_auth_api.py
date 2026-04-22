from __future__ import annotations

import secrets
import urllib.parse
from typing import Optional

import requests

from config import (
    DEFAULT_SCOPES,
    TESLA_AUDIENCE,
    TESLA_AUTHORIZE_URL,
    TESLA_CLIENT_ID,
    TESLA_CLIENT_SECRET,
    TESLA_REDIRECT_URI,
    TESLA_TOKEN_URL,
)
from app.exceptions import TeslaAuthError, TeslaOAuthError


class TeslaCnAuthApi:
    """Manual CN OAuth/token endpoints.

    Reason for existence: the third-party `tesla-fleet-api` library supports CN login URL,
    but its token-exchange and refresh endpoints are currently hard-coded to `.com`.
    """

    def __init__(
        self,
        client_id: str = TESLA_CLIENT_ID,
        client_secret: str = TESLA_CLIENT_SECRET,
        redirect_uri: str = TESLA_REDIRECT_URI,
        authorize_url: str = TESLA_AUTHORIZE_URL,
        token_url: str = TESLA_TOKEN_URL,
        audience: str = TESLA_AUDIENCE,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.audience = audience

    def build_authorize_url(
        self,
        scopes: Optional[list[str]] = None,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        locale: str = "zh-CN",
        prompt: str = "login",
    ) -> dict[str, str]:
        scopes = scopes or list(DEFAULT_SCOPES)
        state = state or secrets.token_urlsafe(24)
        nonce = nonce or secrets.token_urlsafe(24)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "nonce": nonce,
            "locale": locale,
            "prompt": prompt,
            "prompt_missing_scopes": "true",
            "require_requested_scopes": "true",
            "show_keypair_step": "true",
        }
        url = f"{self.authorize_url}?{urllib.parse.urlencode(params)}"
        return {"authorize_url": url, "state": state, "nonce": nonce, "scopes": " ".join(scopes)}

    def get_partner_token(self, scope: Optional[str] = None, timeout: int = 15) -> dict:
        scope = scope or "openid vehicle_device_data vehicle_cmds vehicle_charging_cmds"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": scope,
            "audience": self.audience,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        try:
            resp = requests.post(self.token_url, data=data, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaAuthError(f"Partner token request failed: {exc}") from exc
        return self._parse_json_response(resp, "Get partner token failed")

    def exchange_code(self, code: str, timeout: int = 15) -> dict:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "audience": self.audience,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        try:
            resp = requests.post(self.token_url, data=data, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaOAuthError(f"Exchange code failed: {exc}") from exc
        return self._parse_json_response(resp, "Exchange code failed")

    def refresh_token(self, refresh_token: str, timeout: int = 15) -> dict:
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        try:
            resp = requests.post(self.token_url, data=data, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaOAuthError(f"Refresh token failed: {exc}") from exc
        return self._parse_json_response(resp, "Refresh token failed")

    @staticmethod
    def _parse_json_response(resp: requests.Response, prefix: str) -> dict:
        try:
            data = resp.json()
        except ValueError as exc:
            raise TeslaAuthError(f"{prefix}: non-JSON response, HTTP {resp.status_code}: {resp.text}") from exc
        if not resp.ok:
            message = data.get("error_description") or data.get("error") or str(data)
            raise TeslaAuthError(f"{prefix}, HTTP {resp.status_code}: {message}")
        return data
