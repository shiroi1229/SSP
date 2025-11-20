# UI-v0.5 Evaluation & RAG Visualization PoC レポート

## 実行概要
- 実行コマンド例:  
  `python tools/ui_v0_5_poc_runner.py --base-url http://127.0.0.1:8000 --prompt "UI-v0.5 PoC 用のテストメッセージです。"`  
- ログ: `logs/ui_v0_5_poc.jsonl`

## 実測結果（今回の PoC 実行）
| 項目 | 値 | 評価 |
| --- | --- | --- |
| chat_status | 500 | ❌ バックエンド内部エラー（/api/chat） |
| search_status | 404 | ❌ 該当する RAG 検索 API が未実装 or パス不一致 |
| 評価 UI（フロント） | 画面上では操作可能 | ⚠ API 側とは未連携 |
| RAG Source Graph（フロント） | UI 上では描画される | ⚠ 実データとの完全連携は未検証 |

メモ:  
- PoC ツール（`tools/ui_v0_5_poc_runner.py`）とログ (`logs/ui_v0_5_poc.jsonl`) は稼働しており、「チャット→評価→RAG」のインフラは用意済み。  
- ただし現時点では `/api/chat` が 500、`/api/knowledge/search` が 404 のため、**API 側を直して KPI を満たす作業は別タスクとして追う**。  
- UI-v0.5_PoC は「ツールと手順が揃った段階（結果はまだ赤）」として扱う。

## UI 確認ポイント
1. チャットを送信すると、各メッセージの下に EvaluationPanel が表示され、「Accuracy / Relevance / Naturalness」のスライダーを操作できる。  
2. `Save evaluation` を押すと、パネル右上のスコア表示（平均値）が更新される。  
3. 画面右側またはメッセージ下部に RAG Source Graph が表示され、参照ソース（タイトル・パス・信頼度バー）が並ぶ。  
4. 再読み込みしても直前の平均スコアが scoreCache を通じて再現される（オプション）。

## 所見
- フロントエンドの評価 UI（EvaluationPanel）と RAG Source Graph は実装済みで、UI 上の操作は可能。  
- PoC 用の CLI ツール・ログ・ドキュメントも揃っており、「PoC インフラ」は整備済み。  
- 一方で `/api/chat` の 500 と RAG 検索 API の 404 により、UI-v0.5 の KPI を満たすにはバックエンド側の修正が必要。  
- したがって UI-v0.5_PoC は、「インフラ完成・API 側は別タスクで継続中（結果はまだ赤）」という状態として記録する。
