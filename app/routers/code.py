"""兑换码：用户输入码兑换积分。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RedeemCode, RedeemHistory, User
from ..security import get_current_user

router = APIRouter(prefix="/api/codes", tags=["codes"])


class RedeemReq(BaseModel):
    code: str


@router.post("/redeem")
def redeem(req: RedeemReq, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    code_str = req.code.strip().upper()
    code = db.query(RedeemCode).filter(RedeemCode.code == code_str).first()
    if not code or not code.is_active:
        raise HTTPException(400, "兑换码无效或已停用")
    if code.max_uses > 0 and code.used_count >= code.max_uses:
        raise HTTPException(400, "兑换码已达使用上限")
    already = (
        db.query(RedeemHistory)
        .filter(RedeemHistory.user_id == current_user.id, RedeemHistory.code_id == code.id)
        .first()
    )
    if already:
        raise HTTPException(400, "该兑换码你已兑换过")

    current_user.credits += code.credit_amount
    code.used_count += 1
    db.add(RedeemHistory(user_id=current_user.id, code_id=code.id))
    db.commit()
    return {"ok": True, "credits_now": current_user.credits, "added": code.credit_amount}
