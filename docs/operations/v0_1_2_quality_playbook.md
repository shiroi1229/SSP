# v0.1.2 Quality Playbook

## 目的
- v0.1.1_PoC で収集した KPI を起点に、失敗 33% の原因を分類・把握し、品質基準 (成功率 90%、再生成成功率 80%、ログ損失率 0%、スコア5割合 30%) を満たす段階に進める。
- PoC によって可視化できたメトリクスと SessionLog を活用し、改善前後の数値を定量的に比較できる指標を揃える。

## 改善ターゲット (KPI)
1. 平均応答時間 1.5秒以内
2. 成功率 90%以上
3. 再生成成功率 80%以上
4. ログ損失率 0%
5. スコア5割合 30%以上
6. 失敗レート（status_code >= 400）の内訳をセグメント化し、優先度をつける

## 故障分類と検知方法
- バックエンドの `metrics_logger` で status_code と例外を解析し、`error_tag`・`impact_level` を付与する。
- 想定するタグ:
  - `timeout`：タイムアウト例外や応答なし
  - `upstream_error`：5xx や Prisma/外部 API 例外
  - `validation_error`：400～499
- インパクトレベル:
  - `critical`：5xx / タイムアウト / DB書き込み失敗
  - `high`：4xx
  - `normal`：正常応答

## 実装タスク
1. **error_summary API** (`backend/api/error_summary.py`) を実装し、SessionLog からタグ別エラー件数、インパクト別件数、上位エンドポイントを取得できるようにする。
2. `metrics_logger` に分類ロジックを追加し、SessionLog に `error_tag` / `impact_level` を保存。ミドルウェアは 2xx/4xx/5xx を成功/失敗とみなし、再生成時の成功も計上。
3. `metrics_v0_1` API へ KPI の目標値を含めた JSON を返し、`failure_rate` を追跡。ターゲット達成フラグを入れてダッシュボードが合否を表示できるようにする。
4. **新しいフロントエンドページ** (`frontend/app/analysis/v0_1_quality/page.tsx`) とフック (`hooks/useV0_1Quality.ts`) で、KPI とエラー分類のステータスを表示し、品質状態を俯瞰できるUIを提供。
5. `docs/operations/v0_1_2_quality_playbook.md` をこのプレイブックの説明として整備し、手順をまとめておく。

## 合格基準
- error_summary API でタグ・インパクト・エンドポイントごとの件数が飛び、KPI の failure_rate が正しく計算される。
- フロントエンド品質ページで KPI vs 目標のステータスと、エラータグの一覧・上位エンドポイントが表示される。
- ロードマップの v0.1.2 entry を参照するだけで、どの機能を作るべきかわかるドキュメントがあること。
