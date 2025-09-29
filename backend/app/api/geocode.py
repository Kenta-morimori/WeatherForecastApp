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

    await _respect_rate_limit()
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            resp = await client.get(f"{NOMINATIM_BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
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

    await _respect_rate_limit()
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            resp = await client.get(f"{NOMINATIM_BASE}/reverse", params=params)
            resp.raise_for_status()
            data = resp.json()
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
