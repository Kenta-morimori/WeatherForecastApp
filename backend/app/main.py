import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router as api_router


def _split_env_list(value: str, default: str) -> List[str]:
    raw = value or default
    return [item.strip() for item in raw.split(",") if item.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="WeatherForecastApp API",
        version="0.1.0",
    )

    # ---- CORS settings (env 可変) ----
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
        default="",  # 返却で露出させたいヘッダがあれば指定
    )
    allow_credentials = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        # None を渡さず、常に Sequence[str]（空なら空タプル）を渡す
        expose_headers=tuple(expose_headers),
    )

    # ---- Routes ----
    # /predict を含む API ルーター
    app.include_router(api_router)

    # /healthz: 監視・E2E ヘルスチェック用
    @app.get("/healthz", tags=["meta"])
    def healthz():
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
