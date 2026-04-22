from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import JWT_EXPIRE_HOURS, JWT_SECRET
from app.db import Database
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()
_user_repo = UserRepository(Database())


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = _user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"user_id": user["id"], "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user_from_token(token: str) -> dict:
    """直接从 token 字符串验证用户（用于 query parameter 传递 token 的场景）。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = _user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"user_id": user["id"], "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
