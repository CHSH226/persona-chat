"""后台管理系统 API（需管理员权限）。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Announcement,
    ChatMessage,
    PersonaLayer,
    RedeemCode,
    RedeemHistory,
    User,
)
from ..security import get_current_user, hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _admin_user(user: User):
    if not user.is_admin:
        raise HTTPException(403, "需要管理员权限")
    return user


# ---------- 兑换码 ----------


class CodeCreate(BaseModel):
    code: str = Field(min_length=3)
    credit_amount: int = Field(ge=0)
    max_uses: int = Field(default=0, ge=0)  # 0=无限


@router.get("/codes")
def list_codes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    return [
        {
            "id": c.id,
            "code": c.code,
            "credit_amount": c.credit_amount,
            "max_uses": c.max_uses,
            "used_count": c.used_count,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in db.query(RedeemCode).order_by(RedeemCode.id.desc()).all()
    ]


@router.post("/codes")
def create_code(req: CodeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    code = req.code.strip().upper()
    if db.query(RedeemCode).filter(RedeemCode.code == code).first():
        raise HTTPException(400, "兑换码已存在")
    c = RedeemCode(code=code, credit_amount=req.credit_amount, max_uses=req.max_uses)
    db.add(c)
    db.commit()
    return {"ok": True, "id": c.id}


@router.patch("/codes/{code_id}")
def toggle_code(code_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    c = db.get(RedeemCode, code_id)
    if not c:
        raise HTTPException(404, "不存在")
    c.is_active = not c.is_active
    db.commit()
    return {"ok": True, "is_active": c.is_active}


# ---------- 用户 ----------


@router.get("/users")
def list_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    return [
        {
            "id": u.id,
            "username": u.username,
            "credits": u.credits,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in db.query(User).order_by(User.id).all()
    ]


class CreditPatch(BaseModel):
    credits: int | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    password: str | None = None


@router.patch("/users/{user_id}")
def patch_user(user_id: int, req: CreditPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    if req.credits is not None:
        u.credits = max(0, req.credits)
    if req.is_active is not None:
        u.is_active = req.is_active
    if req.is_admin is not None:
        u.is_admin = req.is_admin
    if req.password:
        u.password_hash = hash_password(req.password)
    db.commit()
    return {"ok": True, "credits": u.credits}


@router.get("/users/{user_id}/chats")
def user_chats(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(ChatMessage.id).all()
    ]


# ---------- 公告 ----------


class AnnouncementCreate(BaseModel):
    content: str


@router.get("/announcements")
def list_announcements(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    return [
        {
            "id": a.id,
            "content": a.content,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in db.query(Announcement).order_by(Announcement.id.desc()).all()
    ]


@router.post("/announcements")
def create_announcement(req: AnnouncementCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    a = Announcement(content=req.content.strip(), is_active=True)
    db.add(a)
    db.commit()
    return {"ok": True, "id": a.id}


@router.patch("/announcements/{ann_id}")
def toggle_announcement(ann_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    a = db.get(Announcement, ann_id)
    if not a:
        raise HTTPException(404, "不存在")
    a.is_active = not a.is_active
    db.commit()
    return {"ok": True, "is_active": a.is_active}


# ---------- 人格层 ----------


class LayerAdminCreate(BaseModel):
    name: str
    type: str = "custom"
    content: str
    weight: float = 1.0
    is_on_demand: bool = False
    keywords: str | None = None
    is_active: bool = True


@router.get("/personas")
def list_personas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    return [
        {
            "id": l.id,
            "name": l.name,
            "type": l.type,
            "weight": l.weight,
            "is_on_demand": l.is_on_demand,
            "keywords": l.keywords,
            "is_active": l.is_active,
            "content": l.content,
        }
        for l in db.query(PersonaLayer).order_by(PersonaLayer.id).all()
    ]


@router.post("/personas")
def create_persona(req: LayerAdminCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    l = PersonaLayer(**req.model_dump(), is_public=True)
    db.add(l)
    db.commit()
    return {"ok": True, "id": l.id}


@router.patch("/personas/{layer_id}")
def patch_persona(layer_id: int, req: LayerAdminCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    l = db.get(PersonaLayer, layer_id)
    if not l:
        raise HTTPException(404, "不存在")
    for k, v in req.model_dump().items():
        setattr(l, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/personas/{layer_id}")
def delete_persona(layer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin_user(user)
    l = db.get(PersonaLayer, layer_id)
    if not l:
        raise HTTPException(404, "不存在")
    db.delete(l)
    db.commit()
    return {"ok": True}
