from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from app.db import Database
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.vehicle_repository import VehicleRepository


class TelemetryService:
    def __init__(self):
        db = Database()
        self.repo = TelemetryRepository(db)
        self.vehicle_repo = VehicleRepository()

    @staticmethod
    def _parse_ts(value) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            v = value.strip()
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(v)
            except ValueError:
                dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError("timestamp is required and must be ISO datetime string")

        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @staticmethod
    def _to_float(value) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return r * c

    def ingest_point(self, user_id: int, payload: dict) -> dict:
        vin = (payload.get("vin") or "").strip()
        if not vin:
            raise ValueError("vin is required")

        if not self.vehicle_repo.get_by_user_id_and_vin(user_id, vin):
            raise ValueError(f"vin={vin} is not bound for current user")

        event_ts = self._parse_ts(payload.get("event_ts") or payload.get("timestamp") or payload.get("ts"))
        speed_kph = self._to_float(payload.get("speed_kph") or payload.get("speed"))
        odometer = self._to_float(payload.get("odometer_km") or payload.get("odometer"))
        odometer_unit = (payload.get("odometer_unit") or "km").lower()
        if odometer is not None and odometer_unit in ("mi", "mile", "miles"):
            odometer *= 1.60934

        battery_level = self._to_float(payload.get("battery_level") or payload.get("soc"))
        latitude = self._to_float(payload.get("latitude") or payload.get("lat"))
        longitude = self._to_float(payload.get("longitude") or payload.get("lon") or payload.get("lng"))

        self.repo.save_point(
            user_id=user_id,
            vin=vin,
            event_ts=event_ts,
            speed_kph=speed_kph,
            odometer_km=odometer,
            battery_level=battery_level,
            latitude=latitude,
            longitude=longitude,
            raw_payload=payload,
        )
        return {"vin": vin, "event_ts": event_ts.strftime("%Y-%m-%d %H:%M:%S")}

    def ingest_batch(self, user_id: int, payloads: list[dict]) -> dict:
        success = 0
        failed = 0
        errors: list[dict] = []
        for idx, payload in enumerate(payloads):
            try:
                self.ingest_point(user_id, payload)
                success += 1
            except Exception as exc:
                failed += 1
                errors.append({"index": idx, "error": str(exc)})
        return {"success_count": success, "failed_count": failed, "errors": errors[:20]}

    def summarize_trips(
        self,
        user_id: int,
        start_ts: datetime,
        end_ts: datetime,
        vin: Optional[str] = None,
        stop_gap_minutes: int = 5,
        limit: int = 20000,
    ) -> dict:
        rows = self.repo.list_points(
            user_id=user_id,
            start_ts=start_ts,
            end_ts=end_ts,
            vin=vin,
            limit=limit,
        )
        trips = self._build_trips(rows, stop_gap_minutes=stop_gap_minutes)

        total_distance_km = round(sum(t["distance_km"] for t in trips), 3)
        total_drive_minutes = round(sum(t["drive_minutes"] for t in trips), 2)
        return {
            "query": {
                "start_ts": start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "end_ts": end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "vin": vin,
                "stop_gap_minutes": stop_gap_minutes,
                "sample_points": len(rows),
            },
            "summary": {
                "trip_count": len(trips),
                "total_distance_km": total_distance_km,
                "total_drive_minutes": total_drive_minutes,
            },
            "trips": trips,
        }

    def _build_trips(self, rows: list[dict], stop_gap_minutes: int = 5) -> list[dict]:
        trips: list[dict] = []
        stop_gap = timedelta(minutes=max(1, stop_gap_minutes))

        grouped: dict[str, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row["vin"], []).append(row)

        for vin, points in grouped.items():
            active = None
            prev = None

            for p in points:
                ts = p["event_ts"]
                speed = self._to_float(p.get("speed_kph")) or 0.0
                moving = speed > 1.0

                if active is None and moving:
                    active = {
                        "vin": vin,
                        "start_ts": ts,
                        "end_ts": ts,
                        "distance_km": 0.0,
                        "drive_seconds": 0.0,
                        "max_speed_kph": speed,
                        "start_battery_level": self._to_float(p.get("battery_level")),
                        "end_battery_level": self._to_float(p.get("battery_level")),
                        "last_moving_ts": ts,
                    }

                if active is not None and prev is not None:
                    prev_ts = prev["event_ts"]
                    dt = (ts - prev_ts).total_seconds()
                    if 0 < dt <= 1800:  # ignore abnormal large gaps
                        seg_km = 0.0
                        prev_odo = self._to_float(prev.get("odometer_km"))
                        curr_odo = self._to_float(p.get("odometer_km"))
                        if prev_odo is not None and curr_odo is not None:
                            delta = curr_odo - prev_odo
                            if 0 <= delta <= 20:
                                seg_km = delta
                        else:
                            lat1 = self._to_float(prev.get("latitude"))
                            lon1 = self._to_float(prev.get("longitude"))
                            lat2 = self._to_float(p.get("latitude"))
                            lon2 = self._to_float(p.get("longitude"))
                            if None not in (lat1, lon1, lat2, lon2):
                                d = self._haversine_km(lat1, lon1, lat2, lon2)
                                if 0 <= d <= 20:
                                    seg_km = d

                        active["distance_km"] += seg_km
                        if moving or (self._to_float(prev.get("speed_kph")) or 0.0) > 1.0:
                            active["drive_seconds"] += dt
                        active["max_speed_kph"] = max(active["max_speed_kph"], speed)
                        active["end_ts"] = ts
                        bl = self._to_float(p.get("battery_level"))
                        if bl is not None:
                            active["end_battery_level"] = bl

                if active is not None and moving:
                    active["last_moving_ts"] = ts

                if active is not None and not moving and active["last_moving_ts"] and (ts - active["last_moving_ts"]) >= stop_gap:
                    trips.append(self._finalize_trip(active))
                    active = None

                prev = p

            if active is not None:
                trips.append(self._finalize_trip(active))

        return trips

    @staticmethod
    def _finalize_trip(trip: dict) -> dict:
        distance_km = round(float(trip["distance_km"]), 3)
        drive_minutes = round(float(trip["drive_seconds"]) / 60.0, 2)
        avg_speed = round((distance_km / (drive_minutes / 60.0)) if drive_minutes > 0 else 0.0, 2)
        start_b = trip.get("start_battery_level")
        end_b = trip.get("end_battery_level")
        battery_used = None
        if start_b is not None and end_b is not None:
            battery_used = round(start_b - end_b, 2)

        return {
            "vin": trip["vin"],
            "start_ts": trip["start_ts"].strftime("%Y-%m-%d %H:%M:%S"),
            "end_ts": trip["end_ts"].strftime("%Y-%m-%d %H:%M:%S"),
            "distance_km": distance_km,
            "drive_minutes": drive_minutes,
            "avg_speed_kph": avg_speed,
            "max_speed_kph": round(float(trip["max_speed_kph"]), 2),
            "start_battery_level": start_b,
            "end_battery_level": end_b,
            "battery_used": battery_used,
        }

