import logging
import os
import sys
from typing import List

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.routes import router as api_router
from .middleware_observability import ObservabilityMiddleware
from .observability import METRICS


def _split_env_list(value: str, default: str) -> List[str]:
    """
    "a,b,c" のようなカンマ区切り環境変数を配列へ。
    空/未設定なら default を使う。
    例:
      ALLOW_ORIGINS="https://your.prod.app,https://your.preview.app,http://localhost:3000"
    """
    raw = value or default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _setup_json_logging() -> None:
    """アプリケーションログを JSON 1行/リクエスト で出す前提の最小設定。"""
    handler = logging.StreamHandler(sys.stdout)
    # JSON文字列をそのまま流すためフォーマッタはメッセージのみ
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def create_app() -> FastAPI:
    _setup_json_logging()

    app = FastAPI(
        title="WeatherForecastApp API",
        version="0.1.0",
    )

    # ---- CORS settings（本番は厳密 Origin を列挙する）----
    allow_origins = _split_env_list(
        os.getenv("ALLOW_ORIGINS", ""),
        default="http://localhost:3000,http://127.0.0.1:3000",
    )
    allow_methods = _split_env_list(
        os.getenv("ALLOW_METHODS", ""),
        default="GET,POST,OPTIONS",
    )
    allow_headers = _split_env_list(
        os.getenv("ALLOW_HEADERS", ""),
        default="*",  # 認証ヘッダ追加などの拡張に備えて *
    )
    expose_headers = _split_env_list(
        os.getenv("EXPOSE_HEADERS", ""),
        default="X-Request-ID",  # Requestトレース用に露出しておく
    )
    allow_credentials = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=tuple(expose_headers),
    )

    # ---- Observability Middleware（構造化ログ + メトリクス）----
    app.add_middleware(ObservabilityMiddleware)

    # ---- Routes ----
    # /predict を含む API ルーター
    app.include_router(api_router)

    # /metrics/simple: 簡易メトリクス（Prometheus互換ではない）
    @app.get("/metrics/simple", tags=["meta"])
    async def metrics_simple():
        return METRICS.snapshot()

    # /health: DoD 用のヘルスチェック（200 を返す）
    @app.get("/health", tags=["meta"])
    def health(resp: Response):
        # X-Request-ID はミドルウェアでも付与されるが、明示的にここでも上書きしない
        return JSONResponse({"status": "ok"})

    # 互換: 既存の /healthz も残す（必要なければ削除可）
    @app.get("/healthz", tags=["meta"])
    def healthz(resp: Response):
        return JSONResponse({"status": "ok"})

    # ---- Error Handlers ----
    # 404 など Starlette 側の HTTPException も {error: ...} で返す
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    # FastAPI 側で raise した HTTPException も {error: ...} で返す
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    return app


app = create_app()
