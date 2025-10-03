from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 相対 import（pytest / uvicorn 両対応）
from ..services.open_meteo import OpenMeteoClient as _OpenMeteoClient
from ..utils import datetime_utils as dtmod

# tests で monkeypatch しやすいように束ねる
OpenMeteoClient = _OpenMeteoClient

router = APIRouter()


# =========================
# /predict（既存踏襲）
# =========================
class PredictRequest(BaseModel):
    lat: float
    lon: float
    tz: str = "Asia/Tokyo"


def _predict_impl(lat: float, lon: float, tz: str) -> Dict[str, Any]:
    d0_date, d1_date = dtmod.local_today_and_tomorrow(tz)
    backend = os.getenv("MODEL_BACKEND", "persistence")

    d1_payload = {"max": 27.0, "min": 21.0, "precip_prob": 0.4, "precip": 2.1}
    d0_payload = {"max": 28.0, "min": 22.0, "precip_prob": 0.3, "precip": 1.2}
    d1_mean = float((d1_payload["max"] + d1_payload["min"]) / 2.0)

    return {
        "backend": backend,
        "date_d0": d0_date.isoformat(),
        "date_d1": d1_date.isoformat(),
        "d0": d0_payload,
        "d1": d1_payload,
        "prediction": {
            "d1_mean": d1_mean,
            "d1_min": d1_payload["min"],
            "d1_max": d1_payload["max"],
            "d1_prec": d1_payload["precip"],
        },
        "forecast_series": [],
        "recent_actuals": [],
    }


@router.post("/predict")
def predict_post(req: PredictRequest):
    return _predict_impl(req.lat, req.lon, req.tz)


@router.get("/predict")
def predict_get(
    lat: float = Query(...),
    lon: float = Query(...),
    tz: str = Query("Asia/Tokyo"),
):
    return _predict_impl(lat, lon, tz)


# =========================
# /forecast（必ず [] を返す・raw は任意）
# =========================
def _format_open_meteo_daily(
    raw: Dict[str, Any] | None, tz: str, days: int, include_raw: bool
) -> Dict[str, Any]:
    src = raw or {}
    daily = (src.get("daily") or {}) if isinstance(src, dict) else {}

    # ★ ここで None を必ず [] に落とす（or [] を使用）
    time = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    precip = daily.get("precipitation_sum") or []

    out: Dict[str, Any] = {
        "latitude": src.get("latitude"),
        "longitude": src.get("longitude"),
        "timezone": (src.get("timezone") or tz),
        "days": int(days),
        "daily": {
            "time": time if isinstance(time, list) else [],
            "tmax": tmax if isinstance(tmax, list) else [],
            "tmin": tmin if isinstance(tmin, list) else [],
            "precip": precip if isinstance(precip, list) else [],
        },
    }
    if include_raw:
        out["raw"] = src
    return out


@router.get("/forecast", tags=["forecast"])
async def forecast_get(
    lat: float = Query(..., ge=-90.0, le=90.0, description="緯度"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="経度"),
    tz: str = Query("Asia/Tokyo", description="IANA timezone 例: Asia/Tokyo"),
    days: int = Query(14, ge=1, le=92, description="過去参照日数（Open-Meteo上限92）"),
    include_raw: bool = Query(False, description="trueで生JSON(raw)も含める"),
) -> Dict[str, Any]:
    """
    直近 days 日の Open-Meteo 日次サマリーを返す。
    - デフォはコンパクト（raw無し）
    - 欠損/nullは必ず空配列にフォールバックし、timezone は tz を保証
    """
    client = OpenMeteoClient(timeout=10.0)
    try:
        raw = await client.fetch_recent_daily(lat=lat, lon=lon, tz=tz, days=days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e!s}")

    return _format_open_meteo_daily(raw, tz=tz, days=days, include_raw=include_raw)
