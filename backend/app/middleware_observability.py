from __future__ import annotations

import json
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .observability import METRICS, get_ext_calls, new_request_context

logger = logging.getLogger("app")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    1リクエスト=1行の構造化JSONログを必ず出す。
    - req_id, method, path, status, latency_ms, ext_api_calls[], client_ip, ua
    - X-Request-ID ヘッダをレスポンスに付与
    - 簡易メトリクス（成功/失敗 / レイテンシ）を in-process に記録
    """

    async def dispatch(self, request: Request, call_next: Callable):
        rid = new_request_context()
        t0 = time.perf_counter()
        status = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            ext_calls = get_ext_calls()
            METRICS.observe(latency_ms=latency_ms, is_error=(status >= 500))

            payload = {
                "ts": int(time.time() * 1000),
                "level": "INFO" if status < 500 else "ERROR",
                "msg": "request",
                "req_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "latency_ms": round(latency_ms, 1),
                "ext_api_calls_count": len(ext_calls),
                "ext_api_calls": ext_calls,  # 配列
                "client_ip": request.client.host if request.client else None,
                "ua": request.headers.get("user-agent"),
            }
            logger.info(json.dumps(payload, ensure_ascii=False))

            # レスポンスに X-Request-ID を付与（エラーでも）
            # call_next で response が得られていない場合でも header を返す
            if response is not None:
                response.headers["X-Request-ID"] = rid
            else:
                response = Response(status_code=status, headers={"X-Request-ID": rid})
