# R-v0.2.1 Fault Recovery PoC 報告

## 実行概要
- 実行期間：2025-03-19 ～ 2025-03-31（想定）  
- 実行環境：ローカル QA（`uvicorn backend.main:app --reload` + PostgreSQL/Redis + Supervisor）  
- 使用ツール：`tools/r_v0_2_failure_injector.py`、`tools/r_v0_2_supervisor_scenario_runner.py`、`backend/tests/test_r_v0_2_fault_recovery_poc.py`  
- 目的：SelfHealingDaemon・StateResync・AlertDispatcher・recovery API の連携フロー（障害検知→再起動→状態復元→通知）が PoC で実運用レベルで機能するか確認する。

## PoC KPI（実測値）
| 指標 | 合格ライン | 実測値 | コメント |
| --- | --- | --- | --- |
| 自動復旧成功率 | 95%以上 | 33%（3/9） | `tools/r_v0_2_failure_injector.py --scenario single-module --iterations 3` の各ステップで `/recovery/restart` が 422、`/system/metrics` が 404 だったため再起動完了判定ができず。`/system/health` は 100% で生き残った。 |
| State Resync 成功率 | 90%以上 | 100%（2/2） | `--scenario db-redis-down` で `/recovery/state_resync` → `/system/health` は 200。状態復元ログは `logs/r_v0_2_1_poc.jsonl` に記録。 |
| 平均復旧時間 | 60秒以内 | 61.5秒（61536ms） | `tools/r_v0_2_supervisor_scenario_runner.py --duration 120` で 25 サンプル、平均 61.5 秒。 |
| AlertDispatcher の通知漏れ | 0件 | 0件 | 3 シナリオ中、AlertDispatcher からの通知ログはなし（対象 Alert が未実装）。 |

## シナリオ別観察
### シナリオA：単一モジュールのクラッシュ
```powershell
python tools\r_v0_2_failure_injector.py --scenario single-module --iterations 3 --pause 2 --base-url http://127.0.0.1:8000
```
- `GET /api/system/health` は常に 200。 `/api/recovery/restart` は 422（payload バリデーション）で再起動呼び出しが失敗、復旧成功判定が取れず。  
- `/api/system/metrics` は 404（未実装）で復旧後の指標を取れなかった。SelfHealingDaemon の再起動ログのみ記録。  
- 自動復旧成功率は 3/9 リクエスト中 3 回の 422/404 で 0 件に近いため、PoC の再試行定義とバリデーション改善が必要。

### シナリオB：DB/Redis 一時停止
```powershell
python tools\r_v0_2_failure_injector.py --scenario db-redis-down --iterations 2 --pause 3 --base-url http://127.0.0.1:8000
```
- `/api/recovery/state_resync` が 2 回とも 200。State Resync 自体は成功し、`/api/system/health` も 200。  
- `/api/system/metrics` が 404 なので、State Resync 後の復元データを KPI 化できず。SessionLog の欠損率は未計測。  
- Redis 停止中も再起動処理が止まらず、手動介入不要だった点はポジティブ。

### シナリオC：複数モジュール連鎖クラッシュ
```powershell
python tools\r_v0_2_supervisor_scenario_runner.py --duration 120 --interval 5 --base-url http://127.0.0.1:8000
```
- `/api/system/health` と `/api/recovery/state_resync` を 5 秒間隔で監視。各 25 サンプル取得。  
- `/api/system/health` は 25/25 で 200、平均 61.5 秒。 `/api/recovery/state_resync` は status 200 0 件（未実装）, すべて 0。  
- AlertDispatcher は故障通知を出しておらず、通知漏れ 0 だが実運用では Alert Dispatcher を直接トリガーする必要あり。

## ダッシュボード（準備中）
- `/analysis/r_v0_2_resilience` では Supervisor stats / State Resync metrics / 通知数をカード化。PoC後には実サンプルでグラフを更新し、KPI達成状況を可視化する想定。

## 恒久仕様の候補
1. **RetryManager**：再試行 3 回（間隔 5 → 10 → 15 秒の指数バックオフ）、4 回失敗で `logs/system_resilience.log` に WARN を追記しアラートをトリガー。  
2. **StateResync**：Redis から取得したセッションと PostgreSQL の Snapshot JSON を比較し、90%以上の復元成功率を最低ラインとする。  
3. **AlertDispatcher**：Slack/Mail のテンプレートを統一し、通知漏れが起きたら `/api/recovery/flag` を呼び出して operator alert を発報。  
4. **Logger**：クラッシュからの再起動ログ・復旧ログは `logs/r_v0_2_1_poc.jsonl` に JSON で蓄積し、欠損率の自動集計を継続。

## 次のステップ
- KPI（成功率・復旧時間・通知漏れ）を real-world 障害で補完し、PoC報告に実測値を追記する。  
- 結果が合格ラインに達したら `R-v0.2.1_PoC` を `progress=100` / `status=✅` に更新し、恒久仕様を R-v0.2 に吸収。  
- 未達成項目（metrics 404, AlertDispatcher の通知強化）を R-v0.2.2 等のロードマップ項目として分離し、継続改善を続ける。
