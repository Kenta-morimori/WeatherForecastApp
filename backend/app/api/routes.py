from datetime import date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# === Pydantic Schemas ===
class PredictRequest(BaseModel):
    lat: float = Field(..., description="Latitude", examples=[35.681236])
    lon: float = Field(..., description="Longitude", examples=[139.767125])
    target_date: date = Field(..., description="Prediction target date (YYYY-MM-DD)")
    name: Optional[str] = Field(None, description="Optional location name label")


class Location(BaseModel):
    lat: float
    lon: float


class Prediction(BaseModel):
    temp_mean_c: float
    temp_min_c: float
    temp_max_c: float
    precip_mm: float


class Explanation(BaseModel):
    features_used: list[str]
    notes: str


class PredictResponse(BaseModel):
    location: Location
    target_date: date
    prediction: Prediction
    explanation: Explanation


# === Routes ===
@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    """
    モック応答（スキーマ準拠）
    将来はここで特徴量生成＋推論を呼び出す
    """
    label = payload.name or f"{payload.lat:.3f},{payload.lon:.3f}"

    return PredictResponse(
        location=Location(lat=payload.lat, lon=payload.lon),
        target_date=payload.target_date,
        prediction=Prediction(
            temp_mean_c=26.8,
            temp_min_c=23.1,
            temp_max_c=30.4,
            precip_mm=4.6,
        ),
        explanation=Explanation(
            features_used=["t_mean_d0", "t_max_d0", "humidity_d0", "wind_u_d0", "pressure_d0"],
            notes=f"ダミー回帰（label={label}）。将来は地域別学習へ置き換え予定。",
        ),
    )
