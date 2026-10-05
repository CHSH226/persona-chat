"""认证：注册 / 登录。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterReq(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class LoginReq(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    name = req.username.strip()
    if db.query(User).filter(User.username == name).first():
        raise HTTPException(400, "用户名已被占用")
    user = User(username=name, password_hash=hash_password(req.password), credits=0, is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.is_admin)
    return {"token": token, "user": {"id": user.id, "username": user.username, "credits": user.credits, "is_admin": user.is_admin}}


@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(400, "用户名或密码错误")
    if not user.is_active:
        raise HTTPException(403, "账号已被禁用")
    token = create_token(user.id, user.is_admin)
    return {"token": token, "user": {"id": user.id, "username": user.username, "credits": user.credits, "is_admin": user.is_admin}}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "credits": current_user.credits, "is_admin": current_user.is_admin}
