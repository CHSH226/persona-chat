from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """用户。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    credits = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class RedeemCode(Base):
    """兑换码：管理员创建，用户兑换积分。"""

    __tablename__ = "redeem_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    credit_amount = Column(Integer, default=0)  # 兑换后获得的积分
    max_uses = Column(Integer, default=0)  # 最大使用次数, 0=无限
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class RedeemHistory(Base):
    """兑换记录：防止同一用户重复兑换同一个码。"""

    __tablename__ = "redeem_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    code_id = Column(Integer, ForeignKey("redeem_codes.id"), index=True)
    created_at = Column(DateTime, default=utcnow)


class Announcement(Base):
    """公告：显示在聊天页顶部。"""

    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class PersonaLayer(Base):
    """人格分层。每个 md 一层，通过权重控制生效程度。"""

    __tablename__ = "persona_layers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 显示名，如 性格 / 经历 / 语气
    type = Column(String, nullable=False)  # personality / experience / tone / knowledge / custom / story
    content = Column(Text, nullable=False)  # md 原文
    weight = Column(Float, default=1.0)  # 0~1，控制生效程度
    is_on_demand = Column(Boolean, default=False)  # True=问到了才按关键词注入
    keywords = Column(Text, nullable=True)  # 按需注入时的关键词，逗号分隔
    is_public = Column(Boolean, default=True)  # 公共层 vs 私有微调层
    owner_id = Column(Integer, nullable=True)  # 私有层归属用户，未来付费微调用
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class ChatMessage(Base):
    """聊天记录。"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    session_key = Column(String, nullable=True, index=True)  # 会话标识
    role = Column(String, nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
