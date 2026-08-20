# v0.5.1 Knowledge Viewer PoC Plan

## Purpose
Knowledge Viewer の永続運用版（v0.5.1）で想定される負荷・検索クエリを PoC ツールで再現し、API 成功率・レスポンス時間・UI 表示の安定性を定量的に確認する。

## Execution environment
1. FastAPI サーバー (`uvicorn backend.main:app --reload`) を `http://127.0.0.1:8000` で起動。
2. Qdrant / PostgreSQL に v0.5 の Knowledge データを投入済み（PoC runner は既存データを前提）。
3. `logs/` 以下に PoC 出力（JSONL + summary）を蓄積するため、書き込み権限を確認。

## Scenarios
- `baseline-load`: `/api/knowledge` を `--limit 20` で連続呼び出しし、平均レスポンスとエラー率を測定。
- `search-mix`: `/api/knowledge/search` に `q` を変えながら呼び出し、スコア・ソースの偏りをログに残す（計測結果から `source_counts` の変化を確認）。
- `filter-switch`: ソースフィルタ（e.g., `source=dispatcher`, `source=insight`）を適用してフロントが想定通り応答するか確認。

## Metrics
| KPI | Goal | Source |
| --- | --- | --- |
| Knowledge API success rate | ≥ 99% | JSONL `status` fields |
| Search p95 latency | < 1.0 秒 | `elapsed_ms` entries |
| Frontend visible errors | 0 件 | ブラウザ console / UI error message |
| Source coverage | at least 3 distinct sources | `source_counts` |

## PoC recipe
1. PoC runner を以下のコマンドで実行（期間・インターバルは要件に応じて調整）。

```bash
python tools/v0_5_1_knowledge_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 5 --interval 2
```

2. PoC runner は `logs/v0_5_1_knowledge_poc.jsonl` へ各サイクルのレスポンスを追記し、`logs/v0_5_1_knowledge_poc_summary.json` で概要を集計する。
3. PoC 終了後、`docs/operations/v0_5_1_poc_report.md` に実測値（total hits, error count, p95 等）と所感を記録して恒久仕様化の判断材料とする。

