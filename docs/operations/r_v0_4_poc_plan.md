# R-v0.4 Adaptive Load Balancer PoC 計画

## PoC の目的
R-v0.4 で実装した Adaptive Load Balancer（`/api/system/metrics` + `/api/system/rebalance`）が、設定したモード（normal/degraded/throttle）を正しく読み込み、再配分リクエストに応じて内部状態を更新できるかを確認します。  
あわせて、モード変更後もメトリクス API が正常応答し続けることを検証します。

## KPI（合格基準）
| 項目 | 目標値 | 検証方法 |
| --- | --- | --- |
| `/api/system/metrics` 応答 | HTTP 200 / JSON | PoC ツールの before/after 両方で確認 |
| `/api/system/rebalance` 応答 | HTTP 200 / JSON | PoC ツールの rebalance 結果で確認 |
| モード更新反映 | `balance.modes` に新モードが反映 | PoC ログ内の `rebalance.balance.modes` を確認 |
| エラー発生 | 0 件（例外でプロセスが落ちない） | PoC 実行中に例外が出ていないこと |

## 実行コマンド
### ① PoC ツールで 1 回実行
```powershell
python tools/r_v0_4_load_balance_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 1
```
- `/api/system/metrics` を叩いて「再配分前」のメトリクスとモードを取得。  
- `/api/system/rebalance` に normal/degraded/throttle の設定を送信してモード定義を上書き。  
- 再度 `/api/system/metrics` を呼び、`balance` フィールドに新しい `modes`/`mode` が反映されているか確認。  
- 結果は `logs/r_v0_4_poc.jsonl` に 1 行追記される。

### ② 繰り返し実行（任意）
```powershell
python tools/r_v0_4_load_balance_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 3
```
- 3 回連続で PoC を回し、モード更新の安定性と API 応答の継続性を確認する。  
- `logs/r_v0_4_poc.jsonl` に 3 行分の記録が残り、`before`/`after` の差分や `rebalance` の内容を比較できる。

## 手順まとめ
1. `python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` でバックエンド起動。  
2. 上記 PoC コマンドを実行して `logs/r_v0_4_poc.jsonl` を生成。  
3. `logs/r_v0_4_poc.jsonl` を開き、`before.balance` と `rebalance.balance` の `modes` が変化していること、`after` で `/api/system/metrics` が正常応答していることを確認。  
4. 必要であれば `frontend/app/monitor/page.tsx` を開き、モニター画面でメトリクスが取得できているかを目視する。  
5. `docs/operations/r_v0_4_poc_report.md` に実測結果と評価を書き込む。

