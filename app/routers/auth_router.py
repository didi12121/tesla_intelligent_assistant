from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import AUTH_PASSWORD_HASH, AUTH_USERNAME
from app.db import Database
from app.repositories.user_repository import UserRepository
from app.services.auth_middleware import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_user_repo = UserRepository(Database())


def _ensure_default_user():
    """首次启动时自动将 config.py 中的默认用户写入数据库。"""
    if not _user_repo.username_exists(AUTH_USERNAME):
        _user_repo.create(AUTH_USERNAME, AUTH_PASSWORD_HASH)


_ensure_default_user()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    user = _user_repo.get_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"success": True, "token": create_token(req.username)}


@router.post("/register")
async def register(req: RegisterRequest):
    if len(req.username) < 2 or len(req.username) > 64:
        raise HTTPException(status_code=400, detail="用户名长度需在 2-64 之间")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    if _user_repo.username_exists(req.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    password_hash = hash_password(req.password)
    _user_repo.create(req.username, password_hash)
    return {"success": True, "message": "注册成功"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"success": True, "user_id": user["user_id"], "username": user["username"]}
