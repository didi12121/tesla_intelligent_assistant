from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from app.db import Database


class TelemetryRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_point(
        self,
        user_id: int,
        vin: str,
        event_ts: datetime,
        speed_kph: Optional[float],
        odometer_km: Optional[float],
        battery_level: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
        raw_payload: dict,
    ) -> int:
        raw_json = json.dumps(raw_payload, ensure_ascii=False)
        return self.db.execute(
            """
            INSERT INTO tesla_vehicle_telemetry
            (user_id, vin, event_ts, speed_kph, odometer_km, battery_level, latitude, longitude, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                vin,
                event_ts,
                speed_kph,
                odometer_km,
                battery_level,
                latitude,
                longitude,
                raw_json,
            ),
        )

    def list_points(
        self,
        user_id: int,
        start_ts: datetime,
        end_ts: datetime,
        vin: Optional[str] = None,
        limit: int = 20000,
    ) -> list[dict]:
        if vin:
            return self.db.fetchall(
                """
                SELECT vin, event_ts, speed_kph, odometer_km, battery_level, latitude, longitude
                FROM tesla_vehicle_telemetry
                WHERE user_id = %s AND vin = %s AND event_ts >= %s AND event_ts <= %s
                ORDER BY vin ASC, event_ts ASC
                LIMIT %s
                """,
                (user_id, vin, start_ts, end_ts, limit),
            )
        return self.db.fetchall(
            """
            SELECT vin, event_ts, speed_kph, odometer_km, battery_level, latitude, longitude
            FROM tesla_vehicle_telemetry
            WHERE user_id = %s AND event_ts >= %s AND event_ts <= %s
            ORDER BY vin ASC, event_ts ASC
            LIMIT %s
            """,
            (user_id, start_ts, end_ts, limit),
        )

