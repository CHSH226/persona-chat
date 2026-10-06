"""persona-chat 主入口：FastAPI + 静态前端托管。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .middleware import SecurityMiddleware
from .routers import admin, announcement, auth, chat, code, persona

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


class NoCacheStaticFiles(StaticFiles):
    """静态前端文件禁用缓存，保证用户每次拉到最新版本。"""

    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return resp


app = FastAPI(title="persona-chat")

Base.metadata.create_all(bind=engine)

app.add_middleware(SecurityMiddleware)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(code.router)
app.include_router(persona.router)
app.include_router(announcement.router)
app.include_router(admin.router)

app.mount("/static", NoCacheStaticFiles(directory=FRONTEND_DIR), name="static")


def _page(html: str):
    resp = FileResponse(FRONTEND_DIR / html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return resp


@app.get("/")
def index():
    return _page("index.html")


@app.get("/chat")
def chat_page():
    return _page("chat.html")


@app.get("/admin")
def admin_page():
    return _page("admin.html")
