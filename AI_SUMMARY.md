### AI Task from issue #28

了解。Gemini CLI 中心で、最短で使い回せる“引き継ぎドキュメント（新規スレッド用プロンプト兼）”をコンパクトにまとめました。

# WeatherForecastApp｜Gemini CLI 簡易運用メモ（新規スレッド用）

## 目的・前提

* **Gemini CLI を継続活用**して軽微修正・冗長削減・テスト追加などを高速化。
* **編集スコープ**は backend/, frontend/, tests/ （将来ディレクトリが増えてもOK）。

## ローカル利用


changed 470 packages in 8s

145 packages are looking for funding
  run `npm fund` for details
0.5.5

* メモ: プロンプト文中の @ は誤解釈されることがあるため、説明で回避（例: “at-sign” と表記）。

## CI（Draft PR 自動生成）

* ワークフロー: 
* 環境:  に secrets 登録（Settings → Environments）。
* **トリガ**: Issue にラベル  / Issue or PR に  コメント / Actions から手動実行。
* 仕組み:

  * ランナーで一時ディレクトリを作成し **パス制限**（backend/, frontend/, tests/）。
  * 変更があれば **Draft PR** を作成（自動マージなし）。 AI_SUMMARY.md に要約を残す。
  * 変更・コミット対象も **パス限定**で安全運用。

## 新規スレッドの初期プロンプト（コピペ用）



## DoD（各タスク）

* 変更は **指定ディレクトリのみ**。
* AI_SUMMARY.md に **### Changes** 追記。
* ローカル: 変更が diff --git a/AI_SUMMARY.md b/AI_SUMMARY.md
index 463b768..0e81889 100644
--- a/AI_SUMMARY.md
+++ b/AI_SUMMARY.md
 @@ -1,40 +1 @@
-### AI Task from issue #24
-
-Title: [gemini-cliテスト] コード全体の冗長箇所チェックと最小リファクタ
-
-## Goal
-- リポジトリ全体（backend/frontend/tests）に対して、冗長・重複・死蔵コード・同値処理の乱立・同一ハードコード値の散在などを検出し、**安全な最小限のリファクタ**で改善する。
-- 変更は既存挙動を保持（ノンブレイキング）。危険度が中〜高の箇所は **提案のみ**（AI_SUMMARY.md）にとどめる。
-
-## Scope
-- 対象ディレクトリ: backend/, frontend/, tests/
-- それ以外（CI, infra, .github配下, package管理, lockファイル 等）は変更しない。
-
-## Must / Constraints
-- **最小変更**：大規模改変・全面リライト・一括フォーマット不可（差分ノイズを避ける）。
-- **API/挙動互換**：外部公開の関数・エンドポイントは互換維持。
-- **依存追加禁止**：新規ライブラリは入れない。
-- **安全ガード**：ファイルごとの変更は小さめ（例：1ファイルあたり±60行以内 / 合計6ファイル以内を目安）。
-- **記号注意**：プロンプト解釈回避のため、デコレータの @ は文中で **at-sign** と表記（コード中はOK）。
-- 変更後は **AI_SUMMARY.md** に 変更内容 を追記（Before/After の要点・影響範囲・リスク・除外した提案を列挙）。
-
-## What to do (優先順)
-1) 検出レポート（AI_SUMMARY.md に追記）
-   - Top 5〜10件の冗長候補を 変更前 と短い根拠で列挙（重複関数/類似処理/コピペ/魔法値の散在/未使用import・未使用関数など）。
-   - 各項目に **推定メリット（行数削減/可読性/保守性）** と **リスク（動作影響/型・UI/外部I/F）** を付記。
-2) **低リスクの機械的リファクタのみ適用**
-   - 例：未使用import・未使用変数の削除 / 定数の共通化 / 極小の重複関数の統合 / 同一パターンの util 化（小規模） / 似た zod/Pydantic スキーマのマージ（完全同値のみ） / 既存のエラーハンドリング方針への揃え など。
-3) 中〜高リスクは **提案のみ**（適用しない）
-   - なぜ今回は適用しないか（依存が多い・UI影響・テスト不足など）を 変更内容 に明記。
-
-## Out of scope（やらないこと）
-- UI/UX仕様変更、設計思想の転換、ルーティングやAPI設計の大幅変更
-- 依存追加/削除、CIやSecretsの編集、リポジトリ設定の変更
-- 大規模フォーマット/命名一括変更/ディレクトリ大移動
-
-## Acceptance Criteria
-- Draft PR が自動生成される。
-- 変更ファイルは backend/, frontend/, tests/ のみ。
-- AI_SUMMARY.md に検出リストと実施/保留の区別が明確に記載されている。
-- 変更は最小で、ビルド/既存テストに影響しないこと（CIがあれば落ちないこと）。
-
-
+### AI Task from issue #28 に反映・基本動作/テストが通る。
* CI: トリガから **Draft PR** が生成される。

## よくある詰まり（超要約）

* **PRが作られない**: Repo → Settings → Actions → **Workflow permissions = Read and write** と **Allow…PR** をON。
* **ModuleNotFoundError**: Uvicornは . を付ける。
* **pathspec エラー**: CI側は存在パスのみ checkout 済み（前提でOK）。
### Changes
* Updated AI_SUMMARY.md with improved documentation for future tasks.