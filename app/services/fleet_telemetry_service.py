from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from config import (
    FLEET_TELEMETRY_PROXY_BASE,
    FLEET_TELEMETRY_PROXY_TIMEOUT,
    FLEET_TELEMETRY_PROXY_VERIFY_SSL,
    TESLA_PARTNER_DOMAIN,
)
from app.services.auth_service import AuthService
from app.services.telemetry_service import TelemetryService
from app.repositories.vehicle_repository import VehicleRepository
from app.tesla.partner_api import PartnerApi


class FleetTelemetryService:
    def __init__(self):
        self.auth_service = AuthService()
        self.vehicle_repo = VehicleRepository()
        self.telemetry_service = TelemetryService()
        self.partner_api = PartnerApi()
        self.proxy_base = FLEET_TELEMETRY_PROXY_BASE.rstrip("/")
        self.proxy_timeout = int(FLEET_TELEMETRY_PROXY_TIMEOUT)
        self.proxy_verify_ssl = bool(FLEET_TELEMETRY_PROXY_VERIFY_SSL)

    def configure(self, user_id: int, vins: list[str], config: dict[str, Any]) -> dict[str, Any]:
        vins = self._resolve_vins(user_id=user_id, vins=vins)
        return self._proxy_request(
            user_id=user_id,
            method="POST",
            path="/api/1/vehicles/fleet_telemetry_config",
            json_body={"vins": vins, "config": config},
        )

    def fleet_status(self, user_id: int, vins: list[str]) -> dict[str, Any]:
        vins = self._resolve_vins(user_id=user_id, vins=vins)
        return self._proxy_request(
            user_id=user_id,
            method="POST",
            path="/api/1/vehicles/fleet_status",
            json_body={"vins": vins},
        )

    def get_vehicle_config(self, user_id: int, vin: str) -> dict[str, Any]:
        self._assert_vin_belongs_to_user(user_id=user_id, vin=vin)
        return self._proxy_request(
            user_id=user_id,
            method="GET",
            path=f"/api/1/vehicles/{vin}/fleet_telemetry_config",
        )

    def delete_vehicle_config(self, user_id: int, vin: str) -> dict[str, Any]:
        self._assert_vin_belongs_to_user(user_id=user_id, vin=vin)
        return self._proxy_request(
            user_id=user_id,
            method="DELETE",
            path=f"/api/1/vehicles/{vin}/fleet_telemetry_config",
        )

    def list_partner_errors(self, domain: str | None = None) -> dict[str, Any]:
        access_token = self.auth_service.ensure_partner_token()
        return self.partner_api.fleet_telemetry_errors(
            domain=domain or TESLA_PARTNER_DOMAIN,
            access_token=access_token,
        )

    def ingest_official_record(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_record(record)
        vin = normalized["vin"]
        vehicle = self.vehicle_repo.get_by_vin(vin)
        if not vehicle:
            raise ValueError(f"vin={vin} is not bound locally")
        return self.telemetry_service.ingest_point(vehicle["user_id"], normalized)

    def _resolve_vins(self, user_id: int, vins: list[str]) -> list[str]:
        clean_vins = [str(v).strip() for v in vins if str(v).strip()]
        if clean_vins:
            for vin in clean_vins:
                self._assert_vin_belongs_to_user(user_id=user_id, vin=vin)
            return clean_vins

        vehicles = self.vehicle_repo.get_by_user_id(user_id)
        result = [v["vin"] for v in vehicles if v.get("vin")]
        if not result:
            raise ValueError("no local vehicles found for current user")
        return result

    def _assert_vin_belongs_to_user(self, user_id: int, vin: str):
        if not self.vehicle_repo.get_by_user_id_and_vin(user_id, vin):
            raise ValueError(f"vin={vin} is not bound for current user")

    def _proxy_request(
        self,
        user_id: int,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        url = f"{self.proxy_base}{path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json_body,
                timeout=self.proxy_timeout,
                verify=self.proxy_verify_ssl,
            )
        except requests.RequestException as exc:
            raise ValueError(f"telemetry proxy request failed: {exc}") from exc

        try:
            data = resp.json()
        except ValueError:
            data = {"raw": resp.text}
        if not resp.ok:
            msg = data.get("error_description") or data.get("error") or data.get("message") or str(data)
            raise ValueError(f"telemetry proxy failed, HTTP {resp.status_code}: {msg}")
        return data

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        vin = str(
            record.get("vin")
            or record.get("VIN")
            or record.get("vehicle_identifier")
            or ""
        ).strip()
        if not vin:
            raise ValueError("vin is required in official telemetry record")

        data = record.get("data") if isinstance(record.get("data"), dict) else {}
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}

        merged: dict[str, Any] = {}
        merged.update(fields)
        merged.update(payload)
        merged.update(data)
        merged.update(record)

        location = merged.get("location") if isinstance(merged.get("location"), dict) else {}
        if not location and isinstance(merged.get("Location"), dict):
            location = merged.get("Location")

        event_ts = (
            merged.get("event_ts")
            or merged.get("timestamp")
            or merged.get("ts")
            or merged.get("recorded_at")
            or merged.get("generated_at")
            or datetime.utcnow().isoformat()
        )

        return {
            "vin": vin,
            "event_ts": event_ts,
            "speed_kph": self._first_number(
                merged,
                ["speed_kph", "speed", "VehicleSpeed", "Speed", "speedKph"],
            ),
            "odometer_km": self._first_number(
                merged,
                ["odometer_km", "odometer", "Odometer", "VehicleOdometer", "odometerKm"],
            ),
            "battery_level": self._first_number(
                merged,
                ["battery_level", "soc", "Soc", "BatteryLevel"],
            ),
            "latitude": self._first_number(
                {**merged, **location},
                ["latitude", "lat", "Latitude"],
            ),
            "longitude": self._first_number(
                {**merged, **location},
                ["longitude", "lon", "lng", "Longitude"],
            ),
            "raw": record,
        }

    @staticmethod
    def _first_number(source: dict[str, Any], keys: list[str]) -> float | None:
        for key in keys:
            value = source.get(key)
            if value is None or value == "":
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None
