# backend/app/middleware_rate_limit.py
from __future__ import annotations

import os
import time
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 単純なトークンバケット（プロセス内、IPベース）
# 目的: /api/* への連打抑止（外部APIの枯渇防止）
_RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))  # 1分あたり
_RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", str(_RATE_LIMIT_PER_MIN)))
_RATE_LIMIT_PATH_PREFIX = os.getenv("RATE_LIMIT_PATH_PREFIX", "/api/")
_RATE_LIMIT_BEHIND_PROXY = os.getenv("RATE_LIMIT_BEHIND_PROXY", "0") in {"1", "true", "TRUE"}

# ip -> (tokens, last_ts)
_BUCKETS: Dict[str, Tuple[float, float]] = {}


def _client_ip(request: Request) -> str:
    if _RATE_LIMIT_BEHIND_PROXY:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 対象外: OPTIONS と prefix外
        if request.method == "OPTIONS" or not request.url.path.startswith(_RATE_LIMIT_PATH_PREFIX):
            return await call_next(request)

        ip = _client_ip(request)
        now = time.time()
        refill_rate_per_sec = _RATE_LIMIT_PER_MIN / 60.0

        tokens, last = _BUCKETS.get(ip, (_RATE_LIMIT_BURST * 1.0, now))
        # トークン補充
        elapsed = max(0.0, now - last)
        tokens = min(_RATE_LIMIT_BURST * 1.0, tokens + elapsed * refill_rate_per_sec)

        if tokens < 1.0:
            # 次に使えるまでの秒数を算出
            wait = int(max(1, (1.0 - tokens) / refill_rate_per_sec))
            headers = {
                "Retry-After": str(wait),
                "X-RateLimit-Limit": str(_RATE_LIMIT_PER_MIN),
                "X-RateLimit-Remaining": "0",
            }
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests (per-IP rate limit)"},
                headers=headers,
            )

        # 消費して通過
        tokens -= 1.0
        _BUCKETS[ip] = (tokens, now)
        response: Response = await call_next(request)
        # メタ情報
        remaining = int(tokens)
        response.headers["X-RateLimit-Limit"] = str(_RATE_LIMIT_PER_MIN)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
