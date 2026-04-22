from __future__ import annotations

import json
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from app.db import Database
from app.services.agent_service import AgentService
from app.services.auth_middleware import get_current_user
from app.services.auth_service import AuthService
from app.services.tts_service import TTSService
from app.services.vehicle_service import VehicleService
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.chat_repository import ChatRepository

router = APIRouter(prefix="/api/agent", tags=["agent"])

agent_service = AgentService()
vehicle_service = VehicleService()
vehicle_repo = VehicleRepository()
auth_service = AuthService()
tts_service = TTSService()
chat_repo = ChatRepository(Database())


class UserLocation(BaseModel):
    latitude: float
    longitude: float

class ChatRequest(BaseModel):
    messages: list[dict]
    vin: str | None = None
    user_location: UserLocation | None = None


class TTSRequest(BaseModel):
    text: str


@router.get("/greeting")
async def greeting(user: dict = Depends(get_current_user)):
    """获取车辆状态并生成打招呼消息。"""
    user_id = user["user_id"]
    try:
        vin = await _get_vin(user_id)
        status = await vehicle_service.vehicle_status(user_id, vin)
        return {"success": True, "vin": vin, "vehicle_status": status}
    except Exception as exc:
        traceback.print_exc()
        return {"success": False, "error": str(exc)}


@router.get("/bind-status")
async def bind_status(user: dict = Depends(get_current_user)):
    """检查用户是否已绑定 Tesla 账号。"""
    user_id = user["user_id"]
    token = auth_service.latest_third_party_token(user_id)
    return {"success": True, "bound": token is not None}


@router.get("/history")
async def history(user: dict = Depends(get_current_user)):
    """获取最近的聊天记录。"""
    user_id = user["user_id"]
    rows = chat_repo.get_recent_messages(user_id, limit=20)
    # 返回顺序：从旧到新
    rows.reverse()
    return {"success": True, "messages": [{"role": r["role"], "content": r["content"]} for r in rows]}


@router.post("/chat")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """SSE 流式聊天。"""
    user_id = user["user_id"]
    try:
        vin = req.vin or await _get_vin(user_id)
        status = await vehicle_service.vehicle_status(user_id, vin)
        user_loc = req.user_location.model_dump() if req.user_location else None

        return StreamingResponse(
            agent_service.chat_stream(req.messages, vin, status, user_id, user_loc, chat_repo),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as exc:
        traceback.print_exc()
        return StreamingResponse(
            _error_stream(str(exc)),
            media_type="text/event-stream",
        )


@router.post("/tts")
async def tts(req: TTSRequest, _: dict = Depends(get_current_user)):
    try:
        audio, media_type = tts_service.synthesize(req.text)
        return Response(content=audio, media_type=media_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")


async def _get_vin(user_id: int) -> str:
    vehicle = vehicle_repo.get_first_by_user_id(user_id)
    if vehicle:
        return vehicle["vin"]
    result = await vehicle_service.list_vehicles(user_id)
    vehicles = result.get("response", [])
    if not vehicles:
        raise Exception("未找到车辆，请先绑定 Tesla 账号")
    return vehicles[0]["vin"]


async def _error_stream(msg: str):
    yield f"data: {json.dumps({'type': 'content', 'content': f'出错了: {msg}'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
