# v0.5.1 Knowledge Viewer PoC Report

## 実行コマンド
```bash
python tools/v0_5_1_knowledge_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 5 --interval 2
```

## 実測 summary
`logs/v0_5_1_knowledge_poc_summary.json` から抜粋（実行後に上書き）。
```json
{
  "last_run": "TBD",
  "iterations": 0,
  "knowledge_hits": 0,
  "search_hits": 0,
  "errors": 0,
  "p95_latency_ms": 0
}
```

## KPI 評価
| KPI | 期待値 | 実測 | 判定 |
| --- | --- | --- | --- |
| `/api/knowledge` 成功率 | ≥ 99% | TBD | TODO |
| `/api/knowledge/search` p95 | < 1000 ms | TBD | TODO |
| フロントエラー | 0 件 | TBD | TODO |
| Source coverage | ≥ 3 sources | TBD | TODO |

## 観察とアクション
1. PoC ツールが `/api/knowledge` と `/api/knowledge/search` を順次叩き、`logs/v0_5_1_knowledge_poc.jsonl` に `status`, `elapsed_ms`, `source` を残す。
2. 実行後の `logs/v0_5_1_knowledge_poc_summary.json` をレビューし、KPI に足りない箇所があれば `modules/rag_engine.py` や Knowledge UI のノイズを調整。
3. 必要あれば `modules/rag_engine.py` の `list_embeddings` / `search` で `source_counts` を増やすためのサンプリング、`frontend/app/analysis/knowledge/page.tsx` で表示ロジックを改善。

