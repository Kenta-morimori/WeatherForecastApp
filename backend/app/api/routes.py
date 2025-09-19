# backend/app/api/routes.py
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..core.time_utils import local_today_and_tomorrow

router = APIRouter()


class PredictRequest(BaseModel):
    lat: float
    lon: float
    tz: str = "Asia/Tokyo"


def _predict_impl(lat: float, lon: float, tz: str):
    # ここは既存の実装に合わせて。以下は例（スタブ）
    d0, d1 = local_today_and_tomorrow(tz)
    # OpenMeteoClient などで取得 → feature_builder → モデル推論 ...
    # 返却スキーマは既存に合わせる
    return {
        "d0": {"max": 28.0, "min": 22.0, "precip_prob": 0.3, "precip": 1.2},
        "d1": {"max": 27.0, "min": 21.0, "precip_prob": 0.4, "precip": 2.1},
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
