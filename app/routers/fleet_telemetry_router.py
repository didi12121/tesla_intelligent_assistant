from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from config import FLEET_TELEMETRY_INGEST_SECRET
from app.services.auth_middleware import get_current_user
from app.services.fleet_telemetry_service import FleetTelemetryService

router = APIRouter(prefix="/api/fleet-telemetry", tags=["fleet-telemetry"])
fleet_telemetry_service = FleetTelemetryService()


class FleetTelemetryConfigureRequest(BaseModel):
    vins: list[str] = Field(default_factory=list)
    config: dict[str, Any]


class FleetTelemetryFleetStatusRequest(BaseModel):
    vins: list[str] = Field(default_factory=list)


class FleetTelemetryIngestRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/configure")
async def configure_telemetry(req: FleetTelemetryConfigureRequest, user: dict = Depends(get_current_user)):
    try:
        data = fleet_telemetry_service.configure(
            user_id=user["user_id"],
            vins=req.vins,
            config=req.config,
        )
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/fleet-status")
async def fleet_status(req: FleetTelemetryFleetStatusRequest, user: dict = Depends(get_current_user)):
    try:
        data = fleet_telemetry_service.fleet_status(
            user_id=user["user_id"],
            vins=req.vins,
        )
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/config/{vin}")
async def get_config(vin: str, user: dict = Depends(get_current_user)):
    try:
        data = fleet_telemetry_service.get_vehicle_config(user_id=user["user_id"], vin=vin)
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/config/{vin}")
async def delete_config(vin: str, user: dict = Depends(get_current_user)):
    try:
        data = fleet_telemetry_service.delete_vehicle_config(user_id=user["user_id"], vin=vin)
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/errors")
async def telemetry_errors(domain: str | None = None, user: dict = Depends(get_current_user)):
    try:
        data = fleet_telemetry_service.list_partner_errors(domain=domain)
        return {"success": True, "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest")
async def ingest_official_telemetry(
    req: FleetTelemetryIngestRequest,
    x_ingest_secret: str | None = Header(default=None, alias="X-Ingest-Secret"),
):
    if FLEET_TELEMETRY_INGEST_SECRET:
        if x_ingest_secret != FLEET_TELEMETRY_INGEST_SECRET:
            raise HTTPException(status_code=401, detail="Invalid ingest secret")

    if not req.items:
        raise HTTPException(status_code=400, detail="items is required")

    success = 0
    failed = 0
    errors: list[dict[str, Any]] = []
    for idx, item in enumerate(req.items):
        try:
            fleet_telemetry_service.ingest_official_record(item)
            success += 1
        except Exception as exc:
            failed += 1
            errors.append({"index": idx, "error": str(exc)})

    return {
        "success": failed == 0,
        "data": {
            "success_count": success,
            "failed_count": failed,
            "errors": errors[:20],
        },
    }


@router.get("/guide")
async def guide():
    return {
        "success": True,
        "data": {
            "configure": {
                "method": "POST",
                "path": "/api/fleet-telemetry/configure",
                "json": {
                    "vins": ["LRWXXXXXXXXXXXXXX"],
                    "config": {
                        "hostname": "telemetry.example.com",
                        "port": 443,
                        "ca": "-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----",
                        "fields": {
                            "VehicleSpeed": 1000,
                            "Odometer": 60000,
                            "Soc": 60000,
                            "Location": {"interval_seconds": 10, "minimum_delta": 10},
                        },
                        "delivery_policy": "latest",
                    },
                },
            },
            "ingest": {
                "method": "POST",
                "path": "/api/fleet-telemetry/ingest",
                "json": {
                    "items": [
                        {
                            "vin": "LRWXXXXXXXXXXXXXX",
                            "timestamp": "2026-04-20T14:30:00Z",
                            "data": {
                                "VehicleSpeed": 35.4,
                                "Odometer": 12345.6,
                                "Soc": 78,
                                "Location": {"latitude": 31.2304, "longitude": 121.4737},
                            },
                        }
                    ]
                },
            },
        },
    }
