import os
from datetime import date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ml.baseline import predict_with_backend

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
    backend = os.getenv("MODEL_BACKEND", "persistence")  # "persistence" | "regression"
    model_path = os.getenv("MODEL_PATH", "./app/model/model.joblib")

    out, explain = predict_with_backend(
        lat=payload.lat,
        lon=payload.lon,
        target_date=payload.target_date,
        backend=backend,
        model_path=model_path,
    )

    return PredictResponse(
        location=Location(lat=payload.lat, lon=payload.lon),
        target_date=payload.target_date,
        prediction=Prediction(
            temp_mean_c=out.temp_mean_c,
            temp_min_c=out.temp_min_c,
            temp_max_c=out.temp_max_c,
            precip_mm=out.precip_mm,
        ),
        explanation=Explanation(
            features_used=explain["features_used"].split(","),
            notes=f"{explain['backend']}: {explain['notes']}",
        ),
    )
