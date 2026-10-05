import os

from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/persona.db")

# 安全
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

# 计费：每条 AI 回复消耗的积分
CREDITS_PER_MESSAGE = 1
