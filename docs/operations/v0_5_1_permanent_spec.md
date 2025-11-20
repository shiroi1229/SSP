# v0.5.1 Knowledge Viewer Permanent

## Goal
v0.5では PoC 的に実装した Knowledge Viewer を、本番に耐える恒久仕様へ引き上げる。大量のコンテキストがあっても操作性が落ちない UI、安定した RAG API、エラー時の回復フロー、そして PoC に耐える監視指標を整備する。

## API surface
- `/api/knowledge`
  - ページング（`limit` + `page`）、ソート（`order_by=created_at|score` + `sort_direction=asc|desc`）をサポート。
  - メタ情報として `total`, `source_counts`, `score_summary` を返し、フロントで絞り込みや KPI 表示を容易にする。
  - `source_filter` が指定された場合はログに記録したうえでサーバー内で絞り込む。
- `/api/knowledge/search`
  - Vector Search を使って `q` でマッチした結果を返し、`limit` + `page` + ソート方向を指定可能。
  - `score_summary` と `source_counts` を返し、PoC KPI 把握用のメトリクスを保持。
  - `log_interaction` で検索クエリと結果数を記録し、PoC での再現を容易にする。
- `/api/knowledge/{id}`
  - Qdrant に格納された Knowledge エントリを ID 指定で取り出す。
  - PoC で検証した予期せぬ 404 に備えて `None` を返すことなく例外情報を記録。

## UI behavior
- 結果カード（`KnowledgeCard`）はスコアに応じたマーカー色、生成日時、ソース、スニペットを含む。
- 一覧ページでは検索／リセット、ソースフィルタ（チップ）、日付／スコアソート、ページング、ページサイズ切り替えを提供。
- 上部で `total entries`, `source count`, `score p95`, `last refreshed` をカード表示し、PoC 実行結果の改札を支援する。
- PoC 情報カード（ドキュメントとツールへのリンク）を表示し、評価担当者が参照先をすぐに開けるようにする。

## KPI（恒久運用）
1. `/api/knowledge`, `/api/knowledge/search` が 99.5% 以上の成功率（4xx/5xx を含まず）。
2. RAG 検索レスポンスタイム (p95) < 800ms。
3. Knowledge UI の操作における JS エラー 0 件（Sentry / console error 対応）。
4. Source ごとのヒット数が取得できること（PoC レポートで `source_counts` を記録）。

## Operational notes
- API は FastAPI ミドルウェア（`metrics_logger` など）でログを残す。
- PoC 実行時は `logs/v0_5_1_knowledge_poc.jsonl` + `logs/v0_5_1_knowledge_poc_summary.json` を参照する。
- PoC で侵害が検出されたソース／スコアの観点は `docs/operations/v0_5_1_poc_report.md` に記録する。

