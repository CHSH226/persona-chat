"""聊天 API：JWT 认证 + 积分检查 + 人格拼接 + 流式调用。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..config import CREDITS_PER_MESSAGE
from ..database import get_db
from ..models import ChatMessage, PersonaLayer, User
from ..security import get_current_user
from ..services.llm import build_system_prompt, stream_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/stream")
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = req.message.strip()
    if not message:
        raise HTTPException(400, "消息不能为空")

    if current_user.credits <= 0:
        raise HTTPException(402, "积分不足，请先兑换积分")

    # 人格层：普通层 + 按需层（按需层命中 user_message 关键词才注入）
    layers = (
        db.query(PersonaLayer)
        .filter(or_(PersonaLayer.is_public == True), PersonaLayer.is_active == True)  # noqa: E712
        .all()
    )
    system_prompt = build_system_prompt(layers, message)

    # 组装历史上下文（最近 20 条）
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.id.desc())
        .limit(20)
        .all()
    )
    history = list(reversed(history))

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})

    # 记录用户输入
    db.add(ChatMessage(user_id=current_user.id, role="user", content=message))
    db.commit()

    async def gen_and_save():
        full = ""
        try:
            async for delta in stream_chat(messages):
                full += delta
                yield delta
        except Exception as e:
            yield f"\n[出错: {e}]"
            full += f"\n[err {e}]"
        finally:
            # 有回复则扣积分 + 存 AI 回复
            if full:
                current_user.credits = max(0, current_user.credits - CREDITS_PER_MESSAGE)
                db.add(ChatMessage(user_id=current_user.id, role="assistant", content=full))
                db.commit()

    return StreamingResponse(gen_and_save(), media_type="text/plain; charset=utf-8")
