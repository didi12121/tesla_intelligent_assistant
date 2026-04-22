from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.auth_middleware import get_current_user
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
telemetry_service = TelemetryService()


class TelemetryPointRequest(BaseModel):
    vin: str
    event_ts: str | None = None
    timestamp: str | None = None
    ts: str | None = None
    speed_kph: float | None = None
    speed: float | None = None
    odometer_km: float | None = None
    odometer: float | None = None
    odometer_unit: str | None = None
    battery_level: float | None = None
    soc: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    lat: float | None = None
    lon: float | None = None
    lng: float | None = None


class TelemetryBatchRequest(BaseModel):
    items: list[TelemetryPointRequest]


@router.post("/ingest")
async def ingest_point(req: TelemetryPointRequest, user: dict = Depends(get_current_user)):
    try:
        data = telemetry_service.ingest_point(user["user_id"], req.model_dump())
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ingest")
async def ingest_point_help():
    return {
        "success": True,
        "message": "Use POST /api/telemetry/ingest with Bearer token to ingest telemetry data.",
        "example": {
            "method": "POST",
            "path": "/api/telemetry/ingest",
            "headers": {"Authorization": "Bearer <jwt-token>"},
            "json": {
                "vin": "LRWxxxxxxxxxxxxx",
                "event_ts": "2026-04-20T14:30:00Z",
                "speed_kph": 36.5,
                "odometer_km": 12345.6,
                "battery_level": 78.0,
                "latitude": 31.2304,
                "longitude": 121.4737,
            },
        },
    }


@router.post("/ingest/batch")
async def ingest_batch(req: TelemetryBatchRequest, user: dict = Depends(get_current_user)):
    try:
        data = telemetry_service.ingest_batch(
            user["user_id"],
            [item.model_dump() for item in req.items],
        )
        return {"success": True, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _parse_query_ts(value: str) -> datetime:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


@router.get("/trips/summary")
async def trip_summary(
    user: dict = Depends(get_current_user),
    start_ts: str | None = Query(default=None, description="ISO datetime"),
    end_ts: str | None = Query(default=None, description="ISO datetime"),
    vin: str | None = Query(default=None),
    stop_gap_minutes: int = Query(default=5, ge=1, le=60),
    limit: int = Query(default=20000, ge=100, le=100000),
):
    try:
        end = _parse_query_ts(end_ts) if end_ts else datetime.now()
        start = _parse_query_ts(start_ts) if start_ts else (end - timedelta(days=7))
        data = telemetry_service.summarize_trips(
            user_id=user["user_id"],
            start_ts=start,
            end_ts=end,
            vin=vin,
            stop_gap_minutes=stop_gap_minutes,
            limit=limit,
        )
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
