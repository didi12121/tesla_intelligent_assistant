from __future__ import annotations

import requests

from config import TESLA_FLEET_API_BASE
from app.exceptions import TeslaPartnerAccountError


class PartnerApi:
    def __init__(self, fleet_api_base: str = TESLA_FLEET_API_BASE):
        self.fleet_api_base = fleet_api_base.rstrip("/")

    def register_partner_account(self, domain: str, access_token: str, timeout: int = 15) -> dict:
        url = f"{self.fleet_api_base}/api/1/partner_accounts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            resp = requests.post(url, json={"domain": domain}, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaPartnerAccountError(f"Register partner account failed: {exc}") from exc
        return self._parse(resp)

    def get_public_key(self, domain: str, access_token: str, timeout: int = 15) -> dict:
        url = f"{self.fleet_api_base}/api/1/partner_accounts/public_key"
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        try:
            resp = requests.get(url, params={"domain": domain}, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaPartnerAccountError(f"Get public key failed: {exc}") from exc
        return self._parse(resp)

    def fleet_telemetry_errors(self, domain: str, access_token: str, timeout: int = 15) -> dict:
        url = f"{self.fleet_api_base}/api/1/partner_accounts/fleet_telemetry_errors"
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        try:
            resp = requests.get(url, params={"domain": domain}, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            raise TeslaPartnerAccountError(f"Get fleet telemetry errors failed: {exc}") from exc
        return self._parse(resp)

    @staticmethod
    def _parse(resp: requests.Response) -> dict:
        try:
            data = resp.json()
        except ValueError as exc:
            raise TeslaPartnerAccountError(f"Partner API returned non-JSON, HTTP {resp.status_code}: {resp.text}") from exc
        if not resp.ok:
            message = data.get("error_description") or data.get("error") or data.get("message") or str(data)
            raise TeslaPartnerAccountError(f"Partner API failed, HTTP {resp.status_code}: {message}")
        return data
