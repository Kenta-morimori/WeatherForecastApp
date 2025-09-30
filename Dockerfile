# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PORT=8000 \
    PYTHONPATH=/app/backend

# uv はビルド時のみ利用（ランタイムでの自動インストールを避ける）
RUN pip install --no-cache-dir uv

# 非rootユーザ（依存解決～実行まで同一ユーザで統一）
RUN useradd -m -u 10001 appuser
WORKDIR /app

# 依存定義のみコピーしてキャッシュ活用
COPY backend/pyproject.toml backend/uv.lock* backend/

# 権限付与してから依存解決（.venv は backend 配下に作成）
RUN chown -R appuser:appuser /app
USER appuser
RUN uv sync --project backend --no-dev --frozen

ENV VIRTUAL_ENV=/app/backend/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# アプリ本体をコピー（.venv を壊さない）
COPY --chown=appuser:appuser backend/ ./backend/

EXPOSE 8000

# ヘルスチェック（RenderのHealth Check Path=/health と合わせる）
HEALTHCHECK CMD python -c "import urllib.request,os; \
    urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health').read()" \
    || exit 1

# ランタイムは venv の uvicorn を直接叩く（余計な同期を発生させない）
CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
