# WeatherForecastApp

> 世界中の任意地点を指定し、**「明日の天気（気温・降水）」をAIモデルで予測**して Web に表示する MVP。

## 🎯 MVP スコープ

- 入力: 地名または地図で選んだ座標（緯度経度）
- 出力: 翌日の **平均気温 / 最高・最低気温 / 降水量** の予測値と、根拠（入力特徴の要約）
- モバイル/デスクトップ対応の 1 画面（検索 → 結果表示）
- 無料データソースのみを使用（API キー不要の範囲を優先）
- 予測はサーバー（FastAPI）で実施し、フロント（Next.js）が表示

## 🏗️ アーキテクチャ概要（ASCII）

```

+------------------------+            +------------------------+
\|        Frontend        |            |        Backend         |
\|  Next.js 14 (TS)       |  HTTP/JSON |  FastAPI (Python 3.11) |
\|  Tailwind + shadcn/ui  +----------->+  /api/predict          |
\|  React Query           |            |  /api/health           |
+-----------+------------+            +-----------+------------+
\|                                     |
\| (lat,lon,date)                      | feature build + inference
\|                                     v
\|                         +-----------+------------+
\|                         |      Data Layer        |
\|                         |  Open-Meteo (forecast) |
\|                         |  Open-Meteo Geocoding  |
\|                         +-----------+------------+
\|                                     |
\|                          +----------v-----------+
\|                          |     ML Model         |
+--------------------------+  (sklearn/LGBM等)    |
\|   \*MVPは軽量回帰     |
+----------------------+

```

## 🔧 技術選定（Why）

- **Next.js 14 (App Router, TS)**: SS/CSR 切替が容易で、開発者体験が良い
- **Tailwind / shadcn/ui**: 最短で整った UI
- **React Query**: API フェッチとキャッシュの定番
- **FastAPI**: 型＆ドキュメント自動生成で API 開発が高速
- **scikit-learn（または LightGBM）**: 小規模データでの回帰に十分
- **Open-Meteo**: API キー不要、地名→座標も提供、非商用 MVP に最適

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
│  └─ lib/       # API クライアント等
├─ backend/
│  └─ app/       # FastAPI アプリ（main.py, routers/）
├─ docs/
│  └─ arch-overview\.md  # 本READMEの詳細版（図、API I/O例）
├─ .github/
│  └─ workflows/ # CI (lint/test/build)
└─ README.md

````

## 🚀 セットアップ & 起動手順（DoD 充足）

> **前提**: Node.js 20 / Python 3.11、（推奨）`pyenv` / `venv`

### 1) Backend（FastAPI）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt  # 無ければ: fastapi "uvicorn[standard]" pydantic scikit-learn httpx pandas numpy
# .env を用意（下記 変数一覧 参照）
uvicorn app.main:app --reload --port 8000
````

* 動作確認: `GET http://127.0.0.1:8000/api/health` → `{"status":"ok"}`

### 2) Frontend（Next.js）

```bash
cd frontend
npm i
# .env.local を用意（下記 変数一覧 参照）
npm run dev
```

* 既定: `http://localhost:3000`
* 画面から地点検索→予測が返れば OK

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

## 📚 用語定義（Glossary）

* **MVP**: 最小実用製品。今回は「翌日の気温/降水を返す」まで
* **Inference**: 学習済みモデルによる推論
* **Feature Engineering**: 外部データを入力特徴に加工する工程
* **Geocoding**: 地名→緯度経度への変換

## 🧪 テスト

* Frontend: `npm run test`（Vitest など） / `npm run lint`（ESLint）
* Backend: `pytest` / `ruff`（lint）

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

* Issue / PR 歓迎。コミット規約とLinterに従ってください。

## 📜 ライセンス

MIT

````

---

# docs/arch-overview.md（新規追加）

```markdown
# Architecture Overview

本ドキュメントは WeatherForecastApp のアーキテクチャ、コンポーネント関係、API I/O をまとめる。

## 1. ハイレベル図

````

Client (Browser)
└─ Next.js App (app/)
├─ 検索フォーム（地名→座標）
├─ 結果カード（気温/降水 + 根拠）
└─ API クライアント（React Query）

FastAPI (backend/app)
├─ Router: /api/predict
├─ Service: feature\_builder.py
├─ Service: model\_infer.py
├─ Client: open\_meteo.py
└─ /api/health

External
├─ Open-Meteo Geocoding API
└─ Open-Meteo Forecast API

````

## 2. コンポーネント

- **Frontend**
  - `app/page.tsx`: 検索 → 結果表示
  - `components/SearchBox.tsx`: 地名入力（Open-Meteo Geocoding を叩くか、バックエンド経由でも可）
  - `lib/api.ts`: `/api/predict` へのクライアント
- **Backend**
  - `app/main.py`: FastAPI エントリ
  - `app/routers/predict.py`: 予測エンドポイント
  - `app/services/feature_builder.py`: Open-Meteo から時系列取得 → 特徴量作成
  - `app/services/model_infer.py`: 学習済みモデル読み込み＆推論
  - `app/clients/open_meteo.py`: 外部APIクライアント

## 3. API 仕様（MVP）

### 3.1 `GET /api/health`

- **Response** `200`
```json
{ "status": "ok" }
````

### 3.2 `POST /api/predict`

* **Request (JSON)**

```json
{
  "lat": 35.681236,
  "lon": 139.767125,
  "target_date": "2025-09-01"
}
```

* **Processing（概要）**

  1. `open_meteo.py` で `lat,lon` の気象データ（当日〜翌日、必要なら直近履歴）取得
  2. `feature_builder.py` で統計量や時間帯別の集約などに加工
  3. `model_infer.py` で回帰推論（MVPは線形回帰やダミーモデル可）
  4. 結果と簡易説明（使用特徴の要約）を返却

* **Response (JSON)**

```json
{
  "location": { "lat": 35.681236, "lon": 139.767125 },
  "target_date": "2025-09-01",
  "prediction": {
    "temp_mean_c": 27.3,
    "temp_min_c": 23.1,
    "temp_max_c": 30.4,
    "precip_mm": 4.6
  },
  "explanation": {
    "features_used": ["t_mean_d0", "t_max_d0", "humidity_d0", "wind_u_d0", "pressure_d0"],
    "notes": "単純回帰（地域共通係数）。今後は地域別学習に切替予定。"
  }
}
```

* **Error 例**

  * `400`: パラメータ不足/不正
  * `502`: 外部API不調
  * `500`: 内部エラー（ログIDを返す）

## 4. データソース

* **Open-Meteo**（API キー不要）

  * Geocoding: `https://geocoding-api.open-meteo.com/v1/search?name={query}`
  * Forecast: `https://api.open-meteo.com/v1/forecast?...`
  * *注意*: レート制限・パラメータ仕様はドキュメントに従うこと

## 5. モデル（MVP）

* 小規模な**汎用回帰モデル**（例：線形回帰、Ridge、LGBM）
* 入力特徴例:

  * 当日（D0）の平均/最大/最小気温、湿度、風、気圧、雲量
  * 季節・月・緯度帯などの単純カテゴリ
* 出力: 翌日（D+1）の平均/最大/最小気温、降水量
* 学習資産が無い間は「単純ルール or ダミー回帰」で疎通確認を優先

## 6. エラーハンドリング / リトライ

* 外部 API: タイムアウト、指数バックオフ、簡易キャッシュ（将来）
* 予測失敗時: 既定メッセージと代替（外部APIの純予報）提示

## 7. セキュリティ / 運用（最小原則）

* CORS: `ALLOW_ORIGINS` で制御
* ログ: 予測要求/応答のサマリ（PII無）を構造化ログで出力
* 将来: CI/CD、APM、Rate Limit、WAF/CDN

## 8. 参考コマンド

### Backend

```bash
uvicorn app.main:app --reload --port 8000
pytest
```

### Frontend

```bash
npm run dev
npm run build && npm run start
```
