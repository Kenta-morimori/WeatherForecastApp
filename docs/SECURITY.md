# Security / Rate Limit & Secrets

## Rate limit (per-IP, per-process)
- `/api/*` は **トークンバケット**でレート制限（env: `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_BURST`）。
- 代理配下の場合は `RATE_LIMIT_BEHIND_PROXY=1`（`X-Forwarded-For` を信頼）を設定。

## Upstream protection
- Nominatim へのアクセスは:
  - **QPS**: `NOMINATIM_QPS` (default 1.0)
  - **Retry**: `HTTP_RETRY_MAX`, `HTTP_RETRY_BACKOFF_S`
  - **Circuit breaker**: `CB_OPEN_THRESHOLD`, `CB_OPEN_WINDOW_S`, `CB_RESET_TIMEOUT_S`

## Secrets hygiene
- `.env*` は gitignore 済み。サンプルは `backend/.env.example` を参照。
- **pre-commit + GitHub Actions** で gitleaks を実行。誤コミットを自動検出。
