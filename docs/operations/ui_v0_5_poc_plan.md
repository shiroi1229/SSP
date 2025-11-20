# UI-v0.5 Evaluation & RAG Visualization PoC 計画

## PoC の目的
UI-v0.5 で実装した「評価 UI（EvaluationPanel）＋RAG Source Graph（SourceGraph）」が、バックエンド API と連動して正しく動作しているかを確認します。  
具体的には、チャット送信 → 評価送信 → RAG 検索の一連の流れが API レベルで成功していること、および UI 上で評価パネルと RAG ソースが表示されることを PoC で確かめます。

## KPI（合格基準）
| 項目 | 目標値 | 検証方法 |
| --- | --- | --- |
| `/api/chat` 成功率 | 100%（PoC 実行中は全て 200） | PoC ツールの `chat_status` を確認 |
| `/api/evaluate` 成功率 | 100% | PoC ツールの `eval_status` を確認 |
| `/api/knowledge/search` 成功率 | 100% | PoC ツールの `search_status` を確認 |
| RAG ソース表示 | references_count ≥ 1 | PoC ログと UI の RAG Source Graph を目視で確認 |

## 実行コマンド
### ① バックエンド起動
```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### ② PoC ツールで API レベルを検証
```powershell
python tools/ui_v0_5_poc_runner.py --base-url http://127.0.0.1:8000 --prompt "UI-v0.5 PoC 用のテストメッセージです。"
```
- `/api/chat` → `/api/evaluate` → `/api/knowledge/search` の 3 つの API を叩き、結果を `logs/ui_v0_5_poc.jsonl` に記録します。  
- ログ内の `chat_status` / `eval_status` / `search_status` がすべて `200` であること、`references_count` が 1 以上であることを確認します。

### ③ UI で評価パネルと RAG Source Graph を確認
1. `npm run dev` でフロントエンドを起動。  
2. `http://localhost:3000/chat` を開き、通常どおりチャットを送信。  
3. 画面下部に表示される EvaluationPanel から、「Accuracy / Relevance / Naturalness」のスライダーを調整して `Save evaluation` をクリック。  
4. 右側または下部に RAG Source Graph が表示され、参照ソースと信頼度がカードとして並んでいることを目視で確認。

## 記録先
- PoC ログ: `logs/ui_v0_5_poc.jsonl`  
- レポート: `docs/operations/ui_v0_5_poc_report.md`

