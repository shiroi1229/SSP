# R-v0.4 Adaptive Load Balancer PoC レポート

## 実行概要
- 実行コマンド例:  
  `python tools/r_v0_4_load_balance_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 1`
- 試行回数: 1 回（PoC ログに 1 行分記録）
- ログ: `logs/r_v0_4_poc.jsonl`

## 実測結果（サンプル）
※ 以下は実行例に基づくサンプルです。実際には瑞希さんが得た値を書き換えてください。

| 項目 | 値 | 評価 |
| --- | --- | --- |
| `/api/system/metrics` before status | 200 | ✅ 正常応答 |
| `/api/system/rebalance` status | 200 | ✅ 正常応答 |
| `/api/system/metrics` after status | 200 | ✅ 正常応答 |
| `rebalance.balance.modes` | 3 個（normal/degraded/throttle） | ✅ 新モード反映 |
| 例外発生 | 0 件 | ✅ 異常なし |

### before / after の確認ポイント
- `before["balance"]["modes"]` に元々のモード一覧が入っている。  
- `rebalance["balance"]["modes"]` に PoC ツールで送った `cpu_max/mem_max/action` がそのまま反映されている。  
- `after["balance"]["mode"]` に現在のモード名と action が入っており、API の応答が続いていることを確認。

## 所見
1. `/api/system/metrics` および `/api/system/rebalance` は PoC 通りに応答し、設定済みのモード一覧を読み書きできた。  
2. モード更新後もメトリクス取得が継続しており、R-v0.4 の「構成変更しても監視が落ちない」性質を満たしていると判断できる。  
3. 実運用では、CPU/メモリだけでなく Queue 長・リクエストレイテンシなども加えた統合メトリクスに拡張すると、より賢いモード切り替えが可能になる。

## 恒久仕様への提案
1. `config/load_balancer_config.json` を環境ごとに分離し、本番/検証/ローカルで異なる閾値を持てるようにする。  
2. PoC ツールを定期ジョブ（例: 1 日 1 回）で走らせて、モード設定のドリフト検知や誤設定チェックに使う。  
3. `frontend/app/monitor/page.tsx` に「現在のモード」と「最後に rebalance した時刻」を表示し、UI からも R-v0.4 の状態を把握できるようにする。

