from __future__ import annotations

import threading
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

# ---- Request-scoped context ----
_req_id: ContextVar[str] = ContextVar("req_id", default="")
_ext_calls: ContextVar[List[Dict[str, Any]]] = ContextVar("ext_calls", default=[])


def new_request_context() -> str:
    rid = uuid.uuid4().hex
    _req_id.set(rid)
    _ext_calls.set([])
    return rid


def get_req_id() -> str:
    rid = _req_id.get()
    return rid or ""


def get_ext_calls() -> List[Dict[str, Any]]:
    return list(_ext_calls.get())


def record_ext_api_call(url: str, status: int, duration_ms: float) -> None:
    calls = _ext_calls.get()
    calls = list(calls)  # copy
    calls.append({"url": url, "status": status, "duration_ms": round(float(duration_ms), 1)})
    _ext_calls.set(calls)


# ---- In-process simple metrics (thread-safe) ----
class SimpleMetrics:
    def __init__(self, max_samples: int = 5000) -> None:
        self.max = max_samples
        self._lock = threading.Lock()
        self._latencies: List[float] = []  # milliseconds
        self._count_total = 0
        self._count_fail = 0

    def observe(self, latency_ms: float, is_error: bool) -> None:
        with self._lock:
            self._count_total += 1
            if is_error:
                self._count_fail += 1
            self._latencies.append(float(latency_ms))
            if len(self._latencies) > self.max:
                drop = len(self._latencies) - self.max
                del self._latencies[0:drop]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            lat = list(self._latencies)
            total = self._count_total
            fail = self._count_fail

        def pct(p: float) -> Optional[float]:
            if not lat:
                return None
            # 最近N件から単純な順位統計で pctl を推定
            k = max(0, min(len(lat) - 1, int(round((p / 100.0) * (len(lat) - 1)))))
            return float(sorted(lat)[k])

        return {
            "requests_total": total,
            "requests_fail": fail,
            "fail_rate": (fail / total) if total else 0.0,
            "latency_ms": {
                "count": len(lat),
                "avg": (sum(lat) / len(lat)) if lat else None,
                "p50": pct(50),
                "p90": pct(90),
                "p95": pct(95),
                "p99": pct(99),
            },
        }


METRICS = SimpleMetrics()


# ---- Helper: timer ----
class TicToc:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.dt = (time.perf_counter() - self.t0) * 1000.0  # ms
