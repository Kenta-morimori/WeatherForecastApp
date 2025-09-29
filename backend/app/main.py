from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.geocode import router as geocode_router
from .api.routes import router as api_router  # /predict, /forecast を提供
from .middleware_observability import ObservabilityMiddleware, metrics_dump, wrap_requests

app = FastAPI(title="WeatherForecastApp API")

# CORS（環境変数 ALLOW_ORIGINS を優先。カンマ区切りで複数指定可）
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allow_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 観測（構造化ログ + 軽量メトリクス）
wrap_requests()
app.add_middleware(ObservabilityMiddleware)

# ルーター配線（ここが無いと /predict が 404）
app.include_router(api_router)
app.include_router(geocode_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/metrics-lite")
def metrics_lite() -> JSONResponse:
    return JSONResponse(metrics_dump())
