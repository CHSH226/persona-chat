"""聊天 API。接收用户消息，拼接人格 prompt，流式调用 DeepSeek。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChatMessage, PersonaLayer
from ..services.llm import build_system_prompt, stream_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_key: str = "default"


@router.post("/stream")
async def chat(req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    message = req.message.strip()
    if not message:
        return {"error": "消息不能为空"}

    # 组装历史上下文 + 当前人格
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == req.session_key)
        .order_by(ChatMessage.id.desc())
        .limit(20)
        .all()
    )
    history = list(reversed(history))

    layers = (
        db.query(PersonaLayer)
        .filter(PersonaLayer.is_public == True, PersonaLayer.is_active == True)  # noqa: E712
        .all()
    )
    system_prompt = build_system_prompt(layers)

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})

    # 记录用户输入
    db.add(ChatMessage(session_key=req.session_key, role="user", content=message))
    db.commit()

    async def gen_and_save():
        try:
            full = ""
            async for delta in stream_chat(messages):
                full += delta
                yield delta
        finally:
            if full:
                db.add(ChatMessage(session_key=req.session_key, role="assistant", content=full))
                db.commit()

    return StreamingResponse(gen_and_save(), media_type="text/plain; charset=utf-8")
