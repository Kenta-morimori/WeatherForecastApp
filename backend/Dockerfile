# backend/Dockerfile
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

WORKDIR /app

# 依存定義だけ先に
COPY backend/pyproject.toml /app/backend/pyproject.toml

# lock 無くてもOK。あれば別途 COPY してもよい
RUN uv sync --project /app/backend || true

# ソース一式
COPY backend/ /app/backend/

# ★ backend を import path に載せる最も明示的な方法
CMD ["uv","run","--project","backend","uvicorn","app.main:app", "--app-dir","backend","--host","0.0.0.0","--port","8000","--loop","uvloop"]
