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

---

## 👥 貢献

Issue / PR 歓迎。Lint/Format に従い、小さな変更でも遠慮なくどうぞ。

---

## 📜 ライセンス

MIT
