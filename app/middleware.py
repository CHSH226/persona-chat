"""全站安全中间件：IP 限流 + 安全响应头。纯标准库实现，无需外部依赖。"""

import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# ---------- 限流规则：路径前缀 -> (每分钟次数, 是否对登录爆破做附加锁定) ----------
RATE_LIMITS = [
    ("/api/chat/stream", 20),
    ("/api/codes/redeem", 5),
    ("/api/auth/register", 3),
    ("/api/auth/login", 5),
]

GLOBAL_IP_LIMIT = 120  # 每个 IP 每分钟全局请求数
WINDOW = 60  # 秒


class RateLimiter:
    def __init__(self):
        # {key: deque[(timestamp, ...)]} 用 dict 存每项的时间戳列表
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, limit: int) -> bool:
        now = time.time()
        window_start = now - WINDOW
        hits = [t for t in self._hits[key] if t > window_start]
        if len(hits) >= limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    # 优先取 X-Forwarded-For（经过反代时），否则取远端地址
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _match_rule(path: str):
    for prefix, limit in RATE_LIMITS:
        if path.startswith(prefix):
            return limit
    return None


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        ip = _client_ip(request)
        now = time.time()

        # 1. 全局 IP 限流（放行静态资源，避免正常加载被限）
        if not path.startswith("/static"):
            if not _limiter.allow(f"g:{ip}", GLOBAL_IP_LIMIT):
                return JSONResponse({"detail": "请求过于频繁，请稍后再试"}, status_code=429)

        # 2. 接口级限流
        limit = _match_rule(path)
        if limit is not None:
            if not _limiter.allow(f"{path}:{ip}", limit):
                return JSONResponse({"detail": "操作过于频繁，请稍后再试"}, status_code=429)

        resp = await call_next(request)

        # 3. 安全响应头
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp
