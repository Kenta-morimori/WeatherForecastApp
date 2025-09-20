# WeatherForecastApp

> 世界中の任意地点を指定し、**「明日の天気（気温・降水）」をAIモデルで予測**して Web に表示する MVP。

## 🎯 MVP スコープ

* 入力: 地名または地図で選んだ座標（緯度経度）
* 出力: 翌日の **平均気温 / 最高・最低気温 / 降水量** の予測値と、根拠（入力特徴の要約）
* モバイル/デスクトップ対応の 1 画面（検索 → 結果表示）
* 無料データソースのみを使用（API キー不要の範囲を優先）
* 予測はサーバー（FastAPI）で実施し、フロント（Next.js）が表示

## 🏗️ アーキテクチャ概要（ASCII）

```
+------------------------+            +------------------------+
|        Frontend        |            |        Backend         |
|  Next.js 14 (TS)       |  HTTP/JSON |  FastAPI (Python 3.11) |
|  Tailwind + shadcn/ui  +----------->+  /api/predict          |
|  React Query           |            |  /api/health           |
+-----------+------------+            +-----------+------------+
            |                                     |
            | (lat,lon,date)                      | feature build + inference
            |                                     v
            |                         +-----------+------------+
            |                         |      Data Layer        |
            |                         |  Open-Meteo (forecast) |
            |                         |  Open-Meteo Geocoding  |
            |                         +-----------+------------+
            |                                     |
            |                          +----------v-----------+
            |                          |     ML Model         |
            +--------------------------+  (sklearn/LGBM等)    |
                                       |   *MVPは軽量回帰     |
                                       +----------------------+
```

## 🔧 技術選定（Why）

* **Next.js 14 (App Router, TS)**: SS/CSR 切替が容易で、開発者体験が良い
* **Tailwind / shadcn/ui**: 最短で整った UI
* **React Query**: API フェッチとキャッシュの定番
* **FastAPI**: 型＆ドキュメント自動生成で API 開発が高速
* **scikit-learn（または LightGBM）**: 小規模データでの回帰に十分
* **Open-Meteo**: API キー不要、地名→座標も提供、非商用 MVP に最適

## 🔄 データフロー

1. フロントで地点検索（Open-Meteo Geocoding）→ 緯度経度を取得
2. フロントが `/api/predict` に `{lat, lon, target_date}` を送信
3. バックエンドで Open-Meteo から必要な予報/直近観測を取得し特徴量に変換
4. 事前学習またはルールベース/単純回帰モデルで翌日の **気温/降水** を推定
5. 推定結果を JSON で返却、フロントでカード表示

## 📁 リポジトリ構成（抜粋）

```
.
├─ frontend/     # Next.js 14 (TypeScript)
│  ├─ app/       # App Router ページ
│  ├─ components/
│  ├─ lib/       # API クライアント等
│  └─ biome.json # Biome 設定
├─ backend/
│  ├─ app/       # FastAPI アプリ（main.py, routers/）
│  └─ pyproject.toml  # uv/依存定義・ツール設定
├─ docs/
│  └─ arch-overview.md  # 本READMEの詳細版（図、API I/O例）
├─ .github/
│  └─ workflows/
│      └─ ci.yml       # CI（pre-commit 実行）
├─ .editorconfig
├─ .gitignore
├─ .pre-commit-config.yaml
└─ README.md
```

## 🚀 セットアップ & 起動手順（DoD 充足）

> **前提**: Node.js 20+ / **pnpm 9+**、Python 3.11+ / **uv**
> 以降は **ローカル/CI共通コマンド**で整形・静的解析が通るよう構成

### 0) 依存導入

```bash
# Frontend 依存
pnpm -C frontend install

# Backend 依存（uv）
uv sync --project backend

# pre-commit をフック登録（uvxで実行）
uvx pre-commit install
```

### 1) Backend（FastAPI）

```bash
# 開発起動（ホットリロード）
uvx uvicorn backend.app.main:app --reload --port 8000
# 動作確認:
# GET http://127.0.0.1:8000/api/health  → {"status":"ok"}
```

### 2) Frontend（Next.js）

```bash
pnpm -C frontend dev
# 既定: http://localhost:3000
# 画面から地点検索→予測が返れば OK
```

### ✅ DoD コマンド（ローカル/CI共通）

```bash
uvx pre-commit run -a
```

## 🔐 環境変数（一覧）

**Frontend (`frontend/.env.local`)**

* `NEXT_PUBLIC_API_BASE_URL` … 例: `http://127.0.0.1:8000`
* `NEXT_PUBLIC_APP_NAME` … 表示用アプリ名（任意）

**Backend (`backend/.env`)**

* `ALLOW_ORIGINS` … CORS 許可（例: `http://localhost:3000`）
* `MODEL_PATH` … 学習済みモデルのパス（例: `./app/model/model.joblib`、未学習時はダミー回帰）
* `OPEN_METEO_BASE` … 例: `https://api.open-meteo.com`
* `OPEN_METEO_GEOCODING` … 例: `https://geocoding-api.open-meteo.com/v1`

> MVPは API キー不要設計（Open-Meteo）。商用化/高精度化時は有料APIやキャッシュ層を追加。

## 🧱 開発基盤（整形 / 静的解析 / フック）

* **Python（backend/）**

  * Lint/Format: `ruff`, `black`, `isort`
  * テスト: `pytest`
  * 実行: `uvx` 経由（バージョン固定・環境差異の最小化）
* **TypeScript（frontend/）**

  * Lint/Format: **Biome**（`pnpm -C frontend biome:check` / `biome:write`）
  * 型検査: `tsc --noEmit`（`pnpm -C frontend typecheck` など）
* **pre-commit（ルート）**

  * `uvx pre-commit run -a` … すべてのフック（Python: ruff/black/isort、TS: Biome、共通: end-of-file/trailing-whitespace 等）を実行
  * CI でも同一コマンドを実行（`.github/workflows/ci.yml`）

## Credits
- Weather data powered by **Open-Meteo** (https://open-meteo.com/).
  本アプリは Open-Meteo の無償APIを利用しています（非商用MVP用途）。

## 📚 用語定義（Glossary）

* **MVP**: 最小実用製品。今回は「翌日の気温/降水を返す」まで
* **Inference**: 学習済みモデルによる推論
* **Feature Engineering**: 外部データを入力特徴に加工する工程
* **Geocoding**: 地名→緯度経度への変換

## 🧪 テスト

* Frontend: `pnpm -C frontend test`（Vitest など） / `pnpm -C frontend lint`（必要に応じて）
* Backend: `uvx pytest` / `uvx ruff check backend`（`--fix` で自動修正）

## 🔧 Backend: 学習→保存→推論（最短手順）

### 1) 学習（GBDT + 残差学習）
```bash
# リポジトリ直下
uv run --project backend python -m app.ml.train --seed 42 --n-days 720 --splits 5 --residual
# => models/YYYYMMDD_<gitSHA>_gbdt.joblib が保存される
```

### 2) モデル切替（推論で使用）

- `backend/.env.example` を参考に `.env` を設定（開発時は export でもOK）
- 例：backend 直下で起動する場合

```bash
cd backend
export MODEL_BACKEND=regression
export MODEL_PATH=./models/<YYYYMMDD>_<gitSHA>_gbdt.joblib
uv run uvicorn app.main:app --reload --port 8000
```

運用のコツ：最新モデルにシンボリックリンクを張る

```bash
# リポジトリ直下
ln -sfn "$(ls models/*_gbdt.joblib | tail -n1)" models/latest_gbdt.joblib
# 起動時は MODEL_PATH=./models/latest_gbdt.joblib で固定
```

### 3) 疎通

```bash
curl -s -X POST 'http://127.0.0.1:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{"lat":35.6762,"lon":139.6503}' | jq
```

## 🧪 CI（GitHub Actions）

- CIは以下を実行
  - pre-commit（ruff/black/isort/Biome）
  - Frontend build（pnpm）
  - Backend pytest（ユニット + E2Eモック）
- 参考: .github/workflows/ci.yml

🌐 環境変数（Backend 抜粋）

- `MODEL_BACKEND`: `persistence` | `regression`（既定: `persistence`）
- `MODEL_PATH`: 学習成果物の `.joblib`（`regression` 時のみ必須）
- `OPEN_METEO_*`: Open-Meteo クライアント設定
- `ALLOW_ORIGINS`: CORS 設定（開発では `http://localhost:3000`）

# 実行手順（コピペ用）

```bash
# 1) 依存
pnpm -C frontend install
uv sync --project backend

# 2) 学習
uv run --project backend python -m app.ml.train --seed 42 --n-days 720 --splits 5 --residual

# 3) モデル切替でAPI起動（backend直下）
cd backend
export MODEL_BACKEND=regression
export MODEL_PATH=./models/$(ls ../models/*_gbdt.joblib | xargs -n1 basename | tail -n1)  # 直近を指す例
uv run uvicorn app.main:app --reload --port 8000

# 4) 疎通
curl -s -X POST 'http://127.0.0.1:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{"lat":35.6762,"lon":139.6503}' | jq

# 5) テスト（任意）
cd ..
uv run --project backend pytest -q
```

## Deployment (Vercel / Frontend)

本プロジェクトのフロントは `frontend/` 配下の Next.js を **Vercel** で自動デプロイする。

### 0. 前提
- リポジトリは GitHub で管理している。
- パッケージマネージャは `pnpm`。
- Vercel GitHub App を **インストール**して、このリポジトリにアクセスを許可する。
  （Vercel ダッシュボード → Add New → Project → Import Git Repository）

### 1. プロジェクト作成（Vercel）
1. Vercel で **New Project** → このリポジトリを選択
2. **Root Directory**: `frontend` を選択（モノレポのため）
3. **Framework Preset**: Next.js（自動検知されることが多い）
4. **Production Branch**: `main` を指定（重要）
5. **Environment Variables**:
   - `NEXT_PUBLIC_API_BASE` を登録（値は運用環境の API ベース URL）
   - 必要に応じて他の `NEXT_PUBLIC_*` を追加
6. **Build & Output**: デフォルトの Next.js 設定でOK（本リポジトリは `frontend/vercel.json` を同梱）
7. **Domains**:
   - Preview は `*.vercel.app` が自動付与
   - 本番用カスタムドメインを使う場合はここで `Production` 側に設定する

### 2. GitHub 連携（Preview URL を PR に表示）
- Vercel GitHub App を有効にすると、PR 作成・更新のたびに **Preview デプロイ**が走り、
  GitHub の PR 画面に **「Vercel — Preview ready」** のチェックと **Preview URL** が表示される。
- チーム開発では、この URL を使ってデザイン/動作確認をレビューする。

### 3. デプロイの挙動（DoD に対応）
- **main へ merge/push**: 自動で **Production デプロイ**が走り、本番 URL が更新される（DoD①）。
- **PR ごと**: 自動で **Preview デプロイ**が作成され、PR 画面に **Preview URL** が表示される（DoD②）。
- モノレポ最適化: `frontend/vercel.json` の `ignoreCommand` により、
  main 以外のブランチでは **`frontend/` に差分が無い PR はスキップ**して無駄なビルドを抑制。

### 4. よくあるハマりどころ
- **Root Directory 未設定**: リポジトリ直下をビルドしに行って失敗する → 必ず `frontend` を選ぶ。
- **環境変数不足**: `NEXT_PUBLIC_*` が未設定で API 呼び出しが失敗 → Vercel の Project Settings で設定。
- **Production Branch 未設定**: main にマージしても本番にならない → `main` を指定する。
- **pnpm のロックファイル**: CI と同様に `pnpm-lock.yaml` をコミットしておくと再現性が高い。

## 📈 将来ロードマップ

* [ ] モデル高度化（時系列外生変数、アンサンブル、地域別バリアント）
* [ ] キャッシュ層 & レート制御（Redis / Cloudflare など）
* [ ] 地図 UI（ドラッグで地点選択、履歴/お気に入り）
* [ ] CI/CD（Actions で frontend/backend のビルド・テスト → デプロイ）
* [ ] 監視（死活監視、APM、フロントのWeb Vitals）
* [ ] i18n（英語/日本語切替）
* [ ] アクセス解析（匿名）

## 🩺 ヘルスチェック

* `GET /api/health` → `{"status":"ok"}` を返せば正常

## 👥 貢献

* Issue / PR 歓迎。コミット規約と Linter に従ってください。

## 📜 ライセンス

MIT
