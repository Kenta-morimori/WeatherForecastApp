from __future__ import annotations

import json
import logging
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextvars import ContextVar
from statistics import median
from typing import Any, Deque, Dict, List

import requests
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# =========
# Contexts
# =========
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
ext_api_calls_ctx: ContextVar[List[Dict[str, Any]]] = ContextVar("ext_api_calls", default=[])

# =========
# Metrics (in-memory / lightweight)
# =========
_MAX_SAMPLES = 1000  # per path


class _PathMetrics:
    __slots__ = ("lat_ms", "req", "fail")

    def __init__(self) -> None:
        self.lat_ms: Deque[int] = deque(maxlen=_MAX_SAMPLES)
        self.req: int = 0
        self.fail: int = 0

    def record(self, latency_ms: int, ok: bool) -> None:
        self.req += 1
        if not ok:
            self.fail += 1
        self.lat_ms.append(latency_ms)

    def snapshot(self) -> Dict[str, Any]:
        arr = list(self.lat_ms)
        arr_sorted = sorted(arr)
        n = len(arr_sorted)

        def _pct(p: float) -> float | None:
            if n == 0:
                return None
            idx = max(0, min(n - 1, int(round((p / 100.0) * (n - 1)))))
            return float(arr_sorted[idx])

        return {
            "requests": self.req,
            "failures": self.fail,
            "failure_rate": (self.fail / self.req) if self.req else 0.0,
            "p50_ms": _pct(50),
            "p95_ms": _pct(95),
            "p99_ms": _pct(99),
            "median_ms": float(median(arr)) if n else None,
            "samples": n,
        }


_METRICS: Dict[str, _PathMetrics] = defaultdict(_PathMetrics)


def metrics_update(path: str, latency_ms: int, ok: bool) -> None:
    _METRICS[path].record(latency_ms, ok)


def metrics_dump() -> Dict[str, Any]:
    overall = _PathMetrics()
    for pm in _METRICS.values():
        # 合成（近似）
        overall.req += pm.req
        overall.fail += pm.fail
        for v in pm.lat_ms:
            overall.lat_ms.append(v)

    by_path = {path: pm.snapshot() for path, pm in _METRICS.items()}
    return {"overall": overall.snapshot(), "by_path": by_path}


# =========
# Logging (JSON / stdlib only)
# =========
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("observability")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt="%(message)s")  # we emit JSON strings
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


LOGGER = _setup_logger()


def log_json(payload: Dict[str, Any]) -> None:
    # ensure_ascii=False で日本語も可読化
    LOGGER.info(json.dumps(payload, ensure_ascii=False))


# =========
# requests instrumentation (monkey-patch)
# =========
def wrap_requests() -> None:
    """
    Wrap requests.Session.request to automatically record external API calls.
    """
    if getattr(requests.Session.request, "_wrapped_by_observability", False):
        return  # already wrapped

    _orig = requests.Session.request

    def _wrapped(self, method, url, *args, **kwargs):
        t0 = time.perf_counter()
        rec = {
            "method": method,
            "url": url,
            "status": None,
            "ok": None,
            "duration_ms": None,
            "error": None,
        }
        try:
            resp = _orig(self, method, url, *args, **kwargs)
            rec["status"] = resp.status_code
            rec["ok"] = bool(200 <= resp.status_code < 400)
            return resp
        except Exception as e:  # noqa: BLE001
            rec["ok"] = False
            rec["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            rec["duration_ms"] = int((time.perf_counter() - t0) * 1000)
            try:
                lst = ext_api_calls_ctx.get()
                # copy-on-write to avoid cross-request contamination
                new = list(lst)
                new.append(rec)
                ext_api_calls_ctx.set(new)
            except LookupError:
                # not within request context
                pass

    _wrapped._wrapped_by_observability = True  # type: ignore[attr-defined]
    requests.Session.request = _wrapped  # type: ignore[assignment]


# =========
# Middleware
# =========
class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    - すべてのリクエストに request_id を付与（レスポンスにもヘッダで返却）
    - レイテンシ計測
    - ext_api_calls（↑の wrap_requests で自動収集）を構造化ログへ集約
    - 簡易メトリクスに記録
    - 1 リクエスト = 1 ログ（追跡容易）
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request_id_ctx.set(rid)
        ext_api_calls_ctx.set([])

        t0 = time.perf_counter()
        status = 500
        exc_text = None
        try:
            response: Response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            exc_text = traceback.format_exc(limit=5)
            raise
        finally:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            ext_calls = ext_api_calls_ctx.get()
            ok = 200 <= status < 400
            metrics_update(request.url.path, latency_ms, ok)

            # レスポンスヘッダ（追跡用）
            try:
                # レスポンスオブジェクトがある場合のみ付与
                response.headers["X-Request-ID"] = rid  # type: ignore[index]
                response.headers["Server-Timing"] = f"app;dur={latency_ms}"  # type: ignore[index]
            except Exception:
                pass

            # 1 リクエスト = 1 行の JSON ログ
            log_json(
                {
                    "type": "request_summary",
                    "request_id": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query or ""),
                    "client": request.client.host if request.client else None,
                    "status": status,
                    "latency_ms": latency_ms,
                    "ext_api_calls_count": len(ext_calls),
                    "ext_api_calls": ext_calls,  # URL/ステータス/所要時間
                    "error": exc_text,
                }
            )
