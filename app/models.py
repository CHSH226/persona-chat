from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class PersonaLayer(Base):
    """人格分层。每个 md 一层，通过权重控制生效程度。"""

    __tablename__ = "persona_layers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 显示名，如 性格 / 经历 / 语气
    type = Column(String, nullable=False)  # personality / experience / tone / knowledge / custom
    content = Column(Text, nullable=False)  # md 原文
    weight = Column(Float, default=1.0)  # 0~1，控制生效程度
    is_public = Column(Boolean, default=True)  # 公共层 vs 私有微调层
    owner_id = Column(Integer, nullable=True)  # 私有层归属用户，未来付费微调用
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class ChatMessage(Base):
    """聊天记录。"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # 预留，未来接入用户系统
    session_key = Column(String, nullable=True, index=True)  # 临时会话标识，用于区分对话
    role = Column(String, nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
