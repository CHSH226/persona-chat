"""认证：注册 / 登录。含输入强校验 + 登录爆破锁定。"""

import re
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 登录爆破锁定：同一 IP 连续失败 N 次锁 15 分钟
LOGIN_LOCK_THRESHOLD = 5
LOCK_SECONDS = 15 * 60
_fail_count = defaultdict(int)
_locked_until = {}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RegisterReq(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class LoginReq(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: RegisterReq, request: Request, db: Session = Depends(get_db)):
    name = req.username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_\u4e00-\u9fa5]+", name):
        raise HTTPException(400, "用户名只能包含字母、数字、下划线或中文")
    if db.query(User).filter(User.username == name).first():
        raise HTTPException(400, "用户名已被占用")
    user = User(username=name, password_hash=hash_password(req.password), credits=0, is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.is_admin)
    return {"token": token, "user": {"id": user.id, "username": user.username, "credits": user.credits, "is_admin": user.is_admin}}


@router.post("/login")
def login(req: LoginReq, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    now = time.time()

    # 爆破锁检查
    if _locked_until.get(ip, 0) > now:
        retry_after = int(_locked_until[ip] - now)
        raise HTTPException(429, f"尝试过于频繁，请 {retry_after // 60 + 1} 分钟后再试")

    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        _fail_count[ip] += 1
        if _fail_count[ip] >= LOGIN_LOCK_THRESHOLD:
            _locked_until[ip] = now + LOCK_SECONDS
            _fail_count[ip] = 0
            raise HTTPException(429, "多次尝试失败，账号已临时锁定 15 分钟")
        raise HTTPException(400, "用户名或密码错误")

    # 成功则重置
    _fail_count[ip] = 0
    _locked_until.pop(ip, None)

    if not user.is_active:
        raise HTTPException(403, "账号已被禁用")
    token = create_token(user.id, user.is_admin)
    return {"token": token, "user": {"id": user.id, "username": user.username, "credits": user.credits, "is_admin": user.is_admin}}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "credits": current_user.credits, "is_admin": current_user.is_admin}
