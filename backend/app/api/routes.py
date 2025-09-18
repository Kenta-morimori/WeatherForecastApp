from __future__ import annotations

import os
from datetime import date as _date
from typing import Dict

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.baseline import SimpleRegModel
from app.services.feature_builder import D0Features, build_d0_features_via_client
from app.services.open_meteo import OpenMeteoClient
from app.utils.datetime_utils import local_today_and_tomorrow

router = APIRouter()


class Health(BaseModel):
    status: str = "ok"


class PredictIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    # 省略時は tz に基づくローカル「今日」を D0 とする
    date: _date | None = None
    # タイムゾーン名（IANA）。既定はアプリの開発想定 "Asia/Tokyo"
    tz: str = "Asia/Tokyo"


class PredictOut(BaseModel):
    backend: str
    date_d0: _date
    date_d1: _date
    features: D0Features
    prediction: Dict[str, float]


@router.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@router.post("/predict", response_model=PredictOut)
def predict(inp: PredictIn) -> PredictOut:
    # --- 日付確定（TZ/DST考慮） ---
    if inp.date:
        d0 = inp.date
        d1 = _date.fromordinal(d0.toordinal() + 1)
    else:
        d0, d1 = local_today_and_tomorrow(inp.tz)

    # --- D0 特徴量（Open-Meteo → 日次集約） ---
    om = OpenMeteoClient()
    try:
        feats: D0Features = build_d0_features_via_client(
            lat=inp.lat, lon=inp.lon, target_date=d0, client=om, tz=inp.tz
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"feature_builder failed: {e}")

    backend = os.getenv("MODEL_BACKEND", "persistence").lower()

    # --- persistence: 翌日=当日 ---
    if backend == "persistence":
        pred = {
            "d1_mean": feats.d0_mean,
            "d1_min": feats.d0_min,
            "d1_max": feats.d0_max,
            "d1_prec": feats.d0_prec,
        }
        return PredictOut(
            backend=backend,
            date_d0=d0,
            date_d1=d1,
            features=feats,
            prediction=pred,
        )

    # --- regression: パイプライン込みモデルで推論 ---
    model_path = os.getenv("MODEL_PATH", "app/model/model.joblib")
    try:
        reg = SimpleRegModel.load(model_path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"failed to load model: {e}")

    df_daily = pd.DataFrame(
        {
            "date": pd.to_datetime([d0]),
            "d_mean": [feats.d0_mean],
            "d_min": [feats.d0_min],
            "d_max": [feats.d0_max],
            "d_prec": [feats.d0_prec],
        }
    )

    try:
        y = reg.predict(df_daily).reshape(-1)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"model predict failed: {e}")

    pred = {
        "d1_mean": float(y[0]),
        "d1_min": float(y[1]),
        "d1_max": float(y[2]),
        "d1_prec": float(y[3]),
    }

    return PredictOut(
        backend="regression",
        date_d0=d0,
        date_d1=d1,
        features=feats,
        prediction=pred,
    )
