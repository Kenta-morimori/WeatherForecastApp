from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .middleware_observability import ObservabilityMiddleware, metrics_dump, wrap_requests

# ===== FastAPI app =====
app = FastAPI(title="WeatherForecastApp API")

# CORS（既存の環境変数を尊重。なければローカル許可）
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allow_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability
wrap_requests()  # requests を自動インストルメント
app.add_middleware(ObservabilityMiddleware)

# ===== Routers / Endpoints =====
# 既存のエンドポイントが別モジュールにある場合は import で登録してください。
# 例:
# from .routers import predict, health
# app.include_router(health.router, prefix="/api")
# app.include_router(predict.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/metrics-lite")
def metrics_lite() -> JSONResponse:
    """
    in-memory 簡易メトリクスのダンプ（失敗率/レイテンシ p50/p95/p99）。
    本番の Prometheus 等の代替ではなく、MVP向けの軽量な観測手段です。
    """
    return JSONResponse(metrics_dump())
