# backend/app/api/geocode.py
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["geocode"])

# ===== 設定 =====
NOMINATIM_BASE = os.getenv("NOMINATIM_BASE", "https://nominatim.openstreetmap.org")
# OSM/Nominatim のポリシー: 識別可能なUA（連絡先）を推奨
NOMINATIM_UA = os.getenv(
    "NOMINATIM_UA",
    "WeatherForecastApp/0.1 (contact: your-email@example.com)",
)
# レート: Nominatimは1 req/sec以上にしない（グローバル）
NOMINATIM_QPS = float(os.getenv("NOMINATIM_QPS", "1.0"))
_MIN_INTERVAL = 1.0 / max(0.1, NOMINATIM_QPS)  # 秒

# HTTP リトライ/CB
HTTP_RETRY_MAX = int(os.getenv("HTTP_RETRY_MAX", "2"))
HTTP_RETRY_BACKOFF_S = float(os.getenv("HTTP_RETRY_BACKOFF_S", "0.3"))
CB_OPEN_THRESHOLD = int(os.getenv("CB_OPEN_THRESHOLD", "5"))  # 失敗回数
CB_OPEN_WINDOW_S = float(os.getenv("CB_OPEN_WINDOW_S", "10.0"))  # 観測窓[s]
CB_RESET_TIMEOUT_S = float(os.getenv("CB_RESET_TIMEOUT_S", "30.0"))  # Open→Half-Openの待機[s]

# 単純なグローバル・レート制御（プロセス内）
_last_call_ts = 0.0
_rate_lock = asyncio.Lock()

# LRU風のメモリキャッシュ（最大 N 件 / TTL秒）
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_ORDER: List[str] = []
_CACHE_MAX = int(os.getenv("GEOCODE_CACHE_MAX", "200"))
_CACHE_TTL = float(os.getenv("GEOCODE_CACHE_TTL", "600"))  # 秒


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    v = _CACHE.get(key)
    if not v:
        return None
    if time.time() - v["_ts"] > _CACHE_TTL:
        _CACHE.pop(key, None)
        try:
            _CACHE_ORDER.remove(key)
        except ValueError:
            pass
        return None
    # LRU更新
    try:
        _CACHE_ORDER.remove(key)
    except ValueError:
        pass
    _CACHE_ORDER.insert(0, key)
    return v["data"]  # dict


def _cache_set(key: str, data: Dict[str, Any]) -> None:
    _CACHE[key] = {"_ts": time.time(), "data": data}
    try:
        _CACHE_ORDER.remove(key)
    except ValueError:
        pass
    _CACHE_ORDER.insert(0, key)
    while len(_CACHE_ORDER) > _CACHE_MAX:
        k = _CACHE_ORDER.pop()
        _CACHE.pop(k, None)


async def _respect_rate_limit() -> None:
    """簡易グローバル QPS 制御"""
    global _last_call_ts
    async with _rate_lock:
        now = time.time()
        elapsed = now - _last_call_ts
        wait = max(0.0, _MIN_INTERVAL - elapsed)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_ts = time.time()


def _to_float(x: Any) -> Optional[float]:
    """Nominatimの値（str/int/float/Noneなど）を安全に float へ変換。失敗時は None。"""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return None
    return None


def _format_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Nominatim JSON v2 の一部だけをフロント用に抽出（型安全変換）"""
    lat = _to_float(item.get("lat"))
    lon = _to_float(item.get("lon"))
    return {
        "name": item.get("name") or item.get("display_name"),
        "display_name": item.get("display_name"),
        "lat": lat,
        "lon": lon,
        "class": item.get("class"),
        "type": item.get("type"),
        "importance": item.get("importance"),
        "bbox": item.get("boundingbox"),
    }


# ===== サーキットブレーカー =====
class CircuitBreaker:
    def __init__(self, threshold: int, window_s: float, reset_timeout_s: float) -> None:
        self.threshold = threshold
        self.window_s = window_s
        self.reset_timeout_s = reset_timeout_s
        self.fail_ts: List[float] = []
        self.state: str = "closed"  # closed | open | half-open
        self.open_since: float = 0.0

    def allow(self) -> bool:
        now = time.time()
        if self.state == "open":
            if now - self.open_since >= self.reset_timeout_s:
                self.state = "half-open"
                return True
            return False
        return True

    def on_success(self) -> None:
        self.fail_ts.clear()
        if self.state in {"half-open", "open"}:
            self.state = "closed"

    def on_failure(self) -> None:
        now = time.time()
        # 窓外の失敗を掃除
        self.fail_ts = [t for t in self.fail_ts if now - t <= self.window_s]
        self.fail_ts.append(now)
        if len(self.fail_ts) >= self.threshold:
            self.state = "open"
            self.open_since = now


_cb_nominatim = CircuitBreaker(CB_OPEN_THRESHOLD, CB_OPEN_WINDOW_S, CB_RESET_TIMEOUT_S)


async def _get_json_with_retry(
    client: httpx.AsyncClient, url: str, *, params: Dict[str, str], headers: Dict[str, str]
) -> Any:
    # サーキットが開いていたら即座に 503
    if not _cb_nominatim.allow():
        raise HTTPException(
            status_code=503, detail="upstream temporarily unavailable (circuit open)"
        )

    last_exc: Optional[Exception] = None
    for attempt in range(HTTP_RETRY_MAX + 1):
        await _respect_rate_limit()
        try:
            resp = await client.get(url, params=params, headers=headers)
            # 429/5xx はリトライ対象
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_exc = HTTPException(
                    status_code=502, detail=f"upstream status {resp.status_code}"
                )
                raise last_exc
            resp.raise_for_status()
            data = resp.json()
            _cb_nominatim.on_success()
            return data
        except Exception as e:
            last_exc = e
            _cb_nominatim.on_failure()
            if attempt < HTTP_RETRY_MAX:
                backoff = min(HTTP_RETRY_BACKOFF_S * (2**attempt), 3.0)
                await asyncio.sleep(backoff)
                continue
            break

    # 最終失敗
    if isinstance(last_exc, HTTPException):
        raise last_exc
    raise HTTPException(status_code=502, detail=f"geocoding upstream error: {last_exc}")


@router.get("/geocode/search")
async def geocode_search(
    q: str = Query(..., min_length=2, description="地名／住所／ランドマーク（例: Tokyo Station）"),
    limit: int = Query(5, ge=1, le=10),
    countrycodes: Optional[str] = Query(None, description="JPなどISO 3166-1 Alpha-2をカンマ区切り"),
    lang: str = Query("ja", description="言語（accept-language）"),
) -> Dict[str, Any]:
    """
    Nominatim でのフォワードジオコーディング（地名→座標）
    - 1req/sec レート制御
    - in-memory LRU キャッシュ
    - 429/5xx リトライ + サーキットブレーカー
    """
    key = f"{q}|{limit}|{countrycodes}|{lang}"
    cached = _cache_get(key)
    if cached:
        return {"q": q, "source": "cache", "results": cached["results"]}

    params: Dict[str, str] = {
        "q": q,
        "format": "jsonv2",
        "limit": str(limit),
        "addressdetails": "1",
    }
    if countrycodes:
        params["countrycodes"] = countrycodes
    headers = {"User-Agent": NOMINATIM_UA, "Accept-Language": lang}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            data = await _get_json_with_retry(
                client, f"{NOMINATIM_BASE}/search", params=params, headers=headers
            )
            if not isinstance(data, list):
                raise HTTPException(status_code=502, detail="unexpected response from nominatim")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"geocoding upstream error: {e}")

    results = [_format_item(x) for x in data if isinstance(x, dict)]
    payload = {"results": results}
    _cache_set(key, payload)
    return {"q": q, "source": "live", **payload}


@router.get("/geocode/reverse")
async def geocode_reverse(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    lang: str = Query("ja"),
) -> Dict[str, Any]:
    """
    リバースジオコーディング（座標→地名）
    """
    key = f"rev|{lat:.5f}|{lon:.5f}|{lang}"
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", **cached}

    params = {"lat": str(lat), "lon": str(lon), "format": "jsonv2", "addressdetails": "1"}
    headers = {"User-Agent": NOMINATIM_UA, "Accept-Language": lang}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            data = await _get_json_with_retry(
                client, f"{NOMINATIM_BASE}/reverse", params=params, headers=headers
            )
            if not isinstance(data, dict):
                raise HTTPException(status_code=502, detail="unexpected response from nominatim")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"reverse geocoding upstream error: {e}")

    result = _format_item(data)
    payload = {"result": result}
    _cache_set(key, payload)
    return {"source": "live", **payload}
