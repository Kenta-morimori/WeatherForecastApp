# WeatherForecastApp

> 世界中の任意地点を指定し、**「明日の天気（気温・降水）」を予測して表示**する MVP。
> 現状はフロントエンドのみで **モックAPI（/predict）** を提供。実バックエンド接続は環境変数で切替。

---

## 🎯 MVP スコープ

* 入力: 地名または座標（緯度経度）
* 出力: 翌日の **最高/最低/平均気温** と **降水量**（将来: 根拠の要約）
* 単一画面（検索 → 結果表示）、モバイル/デスクトップ対応
* まずは **モック応答**で体験を確認 → 後から本APIへ差し替え

---

## 🏗️ アーキテクチャ（現状）

```
+-----------------------------+
| Frontend (Next.js 15 / TS)  |
|  - /forecast  UI            |
|  - /predict   API Route*    |  *モックJSONを返す
+--------------+--------------+
               |
               | (将来) NEXT_PUBLIC_BACKEND_URL を設定すると
               v
+-----------------------------+
| Backend (任意: FastAPI 等)  |
|  - /predict                 |
+-----------------------------+
```

* `NEXT_PUBLIC_BACKEND_URL` **未設定**: フロント内の `/predict`（モック）を叩く
* `NEXT_PUBLIC_BACKEND_URL` **設定**: `https://<backend>/predict` を叩く（CORS要設定）

---

## 🔄 ユーザーフロー

1. `/forecast` で地名 or 緯度経度を入力（現状は緯度経度必須）
2. フロントが `/predict?lat=...&lon=...&tz=...` を **GET**
3. JSON を受け取り、**今日(D0)/明日(D1)** のカードを描画

**モック応答 例**（ブラウザで `/predict?...` を開くと生JSONのみが表示されます）

```json
{
  "d0": {"max": 28.1, "min": 22.4, "precip_prob": 0.31, "precip": 1.8},
  "d1": {"max": 27.1, "min": 21.4, "precip_prob": 0.21, "precip": 0},
  "forecast_series": [],
  "recent_actuals": [],
  "_meta": {"lat": 35.681, "lon": 139.767, "tz": "Asia/Tokyo", "mock": true}
}
```

---

## 📁 リポジトリ構成（抜粋）

```
frontend/
├─ app/
│  ├─ forecast/page.tsx          # 検索フォーム + 結果カード
│  └─ predict/route.ts           # モックAPI（/predict）
├─ src/
│  ├─ components/
│  │  ├─ result-card.tsx
│  │  └─ ui/{button,input,label,card,use-toast}.tsx
│  ├─ lib/
│  │  ├─ api.ts                  # fetchPredict (NEXT_PUBLIC_BACKEND_URL を参照)
│  │  ├─ utils.ts                # cn()
│  │  └─ validation.ts           # zod スキーマ
│  └─ hooks/                     # （必要に応じて）
├─ next.config.ts
└─ package.json
```

---

## 🔧 セットアップ & 起動

> 前提: **Node.js 20+ / pnpm 9+**

```bash
# 依存導入
pnpm -C frontend install

# 開発起動
pnpm -C frontend dev
# → http://localhost:3000/forecast
```

### 環境変数（フロント）

* `NEXT_PUBLIC_BACKEND_URL`（任意）
  未設定ならフロントの `/predict`（モック）を使用。
  設定する場合は **スキーム付き・末尾スラなし**で例: `https://api.example.com`

---

## 🧪 品質チェック（ローカル/CI 共通）

```bash
# Biome / フォーマット・Lint、他 pre-commit フック
uvx pre-commit run -a
# 型チェック（必要なら）
pnpm -C frontend typecheck
```

> Biome の non-null assertion（`!`）等は警告対象です。`?.` で置換してください。

---

## 🚀 デプロイ（Vercel / Frontend）

1. Vercel の **New Project** → 本リポジトリを選択
2. **Root Directory**: `frontend`
3. **Framework Preset**: Next.js（自動検知）
4. **Production Branch**: `main`
5. **Environment Variables**（必要に応じて）

   * `NEXT_PUBLIC_BACKEND_URL` = `https://<your-backend>`
     （モックで良ければ未設定のままでOK）
6. デプロイ後、`/forecast` で動作確認
   `/predict?...` は **生JSONのみ**が出れば正常

> ※ モノレポ最適化をする場合は `vercel.json` の `ignoreCommand` で
> 「`frontend/` に差分がない PR はスキップ」などのチューニングが可能です。

## 📈 運用可観測性（MVP）

本 API は **1 リクエスト＝1 行の JSON 構造化ログ** を出力します（`request_id`, `latency_ms`, `ext_api_calls` を含む）。
また、**簡易メトリクス** を `/api/metrics-lite` で確認できます。

- **DoD**
  - ログ 1 行でリクエストの辿り（`request_id`）が可能
  - 簡易 SLO を明記：**p95 < 800 ms**
    - `/api/metrics-lite` の `overall.p95_ms` が 800 未満であること

### 例：確認コマンド

```bash
# ヘルス
curl -i http://127.0.0.1:8000/api/health

# メトリクス（jq で p95 を確認）
curl -s http://127.0.0.1:8000/api/metrics-lite | jq .overall.p95_ms
```

構造化ログの項目
- request_id: 追跡用 UUID（レスポンスヘッダ X-Request-ID にも付与）
- status: ステータスコード
- latency_ms: リクエスト全体のレイテンシ
- ext_api_calls: アプリ中で発生した外部 API 呼び出し一覧（method,url,status,duration_ms,error）


---

# 使い方・挙動

- **外部 API の自動計測**
  アプリ起動時に `wrap_requests()` が `requests` をモンキーパッチするため、既存コードで `requests.get/post/...` を使っていれば、**追加変更なしで** `ext_api_calls` に計測が載ります。

- **1 リクエスト = 1 ログ**
  `ObservabilityMiddleware` がレイテンシ計測と `request_id` 付与を行い、**最後に 1 行の JSON ログ**を出力します。
  （ログ出力は `stdout`。Render/ Railway/ Koyeb でも収集しやすい形式）

- **簡易メトリクス**
  ルート（`path`）ごとに過去最大 1000 件のレイテンシを保持し、`p50/p95/p99` と `failure_rate` を計算して `/api/metrics-lite` で返します。
  本格運用では Prometheus + Grafana 等へ置き換え想定の**簡易版**です。

---

# 動作確認（ローカル）

```bash
# 起動（例）
uvx uvicorn backend.app.main:app --reload --port 8000

# 疑似トラフィックを流してメトリクス確認
for i in $(seq 1 20); do curl -s 'http://127.0.0.1:8000/api/health' > /dev/null; done
curl -s 'http://127.0.0.1:8000/api/metrics-lite' | jq .
ログ例（1 行／1 リクエスト）:

```json
コードをコピーする
{
  "type":"request_summary",
  "request_id":"b2f5c2c3-...-8a27",
  "method":"GET",
  "path":"/api/health",
  "status":200,
  "latency_ms":3,
  "ext_api_calls_count":0,
  "ext_api_calls":[]
}
```

---

## 🔌 バックエンドをつなぐ時（任意）

* 期待するエンドポイント: `GET /predict?lat=<num>&lon=<num>&tz=<IANA TZ>`
* 返却 JSON は上記モックと同形が望ましい
* CORS: フロント配信元（Vercel の Preview/Production ドメイン）を許可

---

## 📈 ロードマップ

* [ ] 地名 → 座標のジオコーディング（UI/自動補完）
* [ ] 折れ線チャート（`forecast_series` / `recent_actuals` の可視化）
* [ ] 実API接続（FastAPI 等）+ 推論ロジック
* [ ] 入力バリデーション拡充・エラーメッセージ整備
* [ ] E2E テスト / モバイル最適化の微調整

## 地名検索 / 地図ピッカー（規約・レート）

- 本アプリのジオコーディングは既定で **Nominatim (OpenStreetMap)** を使用します。
- **遵守事項**：
  - 1 リクエスト/秒以下（アプリ内でスロットルしています）
  - 連絡先を含む **識別可能な User-Agent** を送信（`NOMINATIM_UA` 環境変数）
  - 大量アクセス/商用は **自前Nominatim** か **Mapbox/Google 等の商用API**利用を検討
  - 地図タイルには OSM の帰属表記（Attribution）を表示
- **環境変数**
  - `NEXT_PUBLIC_API_BASE`（フロント→バックのベースURL）
  - `NOMINATIM_BASE` / `NOMINATIM_UA` / `NOMINATIM_QPS` / `GEOCODE_CACHE_MAX` / `GEOCODE_CACHE_TTL`

---

## 👥 貢献

Issue / PR 歓迎。Lint/Format に従い、小さな変更でも遠慮なくどうぞ。

---

## 📜 ライセンス

MIT
