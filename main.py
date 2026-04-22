from __future__ import annotations

import os
import traceback

from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from config import CORS_ALLOW_ORIGINS
from app.services.auth_service import AuthService
from app.services.auth_middleware import get_current_user
from app.services.vehicle_service import VehicleService
from app.routers.agent_router import router as agent_router
from app.routers.auth_router import router as auth_router
from app.routers.fleet_telemetry_router import router as fleet_telemetry_router
from app.routers.telemetry_router import router as telemetry_router

app = FastAPI(title="Tesla CN OAuth Callback Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(telemetry_router)
app.include_router(fleet_telemetry_router)

auth_service = AuthService()
vehicle_service = VehicleService()


@app.get("/")
def index():
    return {
        "success": True,
        "message": "Tesla CN callback service is running",
        "routes": [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/me",
            "/tesla/login",
            "/tesla/login-redirect",
            "/tesla/callback",
            "/tesla/partner/setup",
            "/tesla/partner/public-key",
            "/tesla/init",
            "/tesla/vehicles",
            "/tesla/vehicles/{vin}/lock",
            "/tesla/vehicles/{vin}/unlock",
            "/tesla/vehicles/{vin}/trunk/{rear|front}",
            "/tesla/vehicles/{vin}/status",
            "/api/telemetry/ingest",
            "/api/telemetry/ingest/batch",
            "/api/telemetry/trips/summary",
            "/api/fleet-telemetry/guide",
            "/api/fleet-telemetry/configure",
            "/api/fleet-telemetry/fleet-status",
            "/api/fleet-telemetry/config/{vin}",
            "/api/fleet-telemetry/errors",
            "/api/fleet-telemetry/ingest",
        ],
    }


@app.get("/tesla/login")
def tesla_login(user: dict = Depends(get_current_user)):
    try:
        data = auth_service.build_authorize_url(user_id=user["user_id"])
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/login-redirect")
def tesla_login_redirect(token: str = Query(default=None)):
    """Tesla OAuth 授权跳转。token 通过 query parameter 传递（因为 window.open 无法发送 headers）。"""
    from app.services.auth_middleware import get_current_user_from_token
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    user = get_current_user_from_token(token)
    data = auth_service.build_authorize_url(user_id=user["user_id"])
    return RedirectResponse(url=data["authorize_url"], status_code=302)


@app.get("/tesla/partner/setup")
def partner_setup():
    try:
        result = auth_service.register_partner_account()
        return {"success": True, "data": result}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/partner/public-key")
def partner_public_key_sync():
    try:
        result = auth_service.sync_partner_public_key()
        return {"success": True, "data": result}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/init")
def tesla_init():
    try:
        result = auth_service.initialize_partner()
        return {"success": True, "data": result}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/callback", response_class=RedirectResponse)
def tesla_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    try:
        if error:
            if state:
                try:
                    auth_service.mark_oauth_failure(state, f"{error}: {error_description or ''}".strip())
                except Exception:
                    pass
            return RedirectResponse(url=f"/?auth_error={error}", status_code=302)

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state")

        auth_service.exchange_code_for_token(code=code, state=state)
        # 授权成功后重定向回前端首页
        return RedirectResponse(url="/?auth_success=1", status_code=302)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        return RedirectResponse(url=f"/?auth_error=callback_failed", status_code=302)


@app.get("/tesla/token/latest")
def latest_token(user: dict = Depends(get_current_user)):
    data = auth_service.latest_third_party_token(user["user_id"])
    return {"success": bool(data), "data": data}


@app.get("/tesla/vehicles")
async def list_vehicles(user: dict = Depends(get_current_user)):
    try:
        data = await vehicle_service.list_vehicles(user["user_id"])
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/vehicles/{vin}/lock")
async def lock_vehicle(vin: str = Path(...), user: dict = Depends(get_current_user)):
    try:
        data = await vehicle_service.lock_doors(user["user_id"], vin)
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/vehicles/{vin}/unlock")
async def unlock_vehicle(vin: str = Path(...), user: dict = Depends(get_current_user)):
    try:
        data = await vehicle_service.unlock_doors(user["user_id"], vin)
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/vehicles/{vin}/trunk/{which_trunk}")
async def actuate_trunk(vin: str = Path(...), which_trunk: str = Path(...), user: dict = Depends(get_current_user)):
    if which_trunk not in ("rear", "front"):
        raise HTTPException(status_code=400, detail="which_trunk must be 'rear' or 'front'")
    try:
        data = await vehicle_service.actuate_trunk(user["user_id"], vin, which_trunk)
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/vehicles/{vin}/status")
async def vehicle_status(vin: str = Path(...), user: dict = Depends(get_current_user)):
    try:
        data = await vehicle_service.vehicle_status(user["user_id"], vin)
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tesla/vehicles/{vin}/fleet-status")
async def check_fleet_status(vin: str = Path(...), user: dict = Depends(get_current_user)):
    try:
        data = await vehicle_service.check_fleet_status(user["user_id"], [vin])
        return {"success": True, "data": data}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


# Serve Vue SPA static files (must be after all API routes)
_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
