# backend/app/main.py
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from .api.geocode import router as geocode_router  # /geocode/search, /geocode/reverse
from .api.routes import router as api_router  # /predict, /forecast
from .middleware_observability import ObservabilityMiddleware, metrics_dump, wrap_requests

app = FastAPI(title="WeatherForecastApp API")

# ----- CORS -----
# 環境変数 ALLOW_ORIGINS をカンマ区切りで指定（例: "http://localhost:3000,https://*.vercel.app"）
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allow_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- 観測（構造化ログ + 軽量メトリクス） -----
wrap_requests()
app.add_middleware(ObservabilityMiddleware)

# ----- ルーター配線 -----
# ここが無いと /predict や /forecast が 404
app.include_router(api_router)  # /predict, /forecast
# geocode は /api 配下に公開（→ /api/geocode/search, /api/geocode/reverse）
app.include_router(geocode_router, prefix="/api")


# ----- Health / Metrics -----
# Render のヘルスチェックと合わせて /health を公開（互換で /api/health も残す）
@app.get("/health")
def health_root() -> dict:
    return {"status": "ok"}


@app.get("/api/health")
def health_api() -> dict:
    return {"status": "ok"}


@app.get("/api/metrics-lite")
def metrics_lite() -> JSONResponse:
    return JSONResponse(metrics_dump())


# ----- 起動時にルート一覧を出力（デバッグ用） -----
@app.on_event("startup")
async def _log_routes_on_startup() -> None:
    if os.getenv("LOG_ROUTES") == "1":
        for r in app.routes:
            if isinstance(r, APIRoute):
                # 例: ROUTE ['GET'] /api/geocode/search
                print("ROUTE", sorted(r.methods), r.path)
