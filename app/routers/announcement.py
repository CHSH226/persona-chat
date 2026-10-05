"""公开公告：聊页顶部实时显示启用中的公告。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Announcement

router = APIRouter(prefix="/api", tags=["announcement"])


@router.get("/announcements/active")
def active_announcements(db: Session = Depends(get_db)):
    return [
        {"id": a.id, "content": a.content, "created_at": a.created_at.isoformat() if a.created_at else None}
        for a in db.query(Announcement).filter(Announcement.is_active == True).order_by(Announcement.id.desc()).all()  # noqa: E712
    ]
