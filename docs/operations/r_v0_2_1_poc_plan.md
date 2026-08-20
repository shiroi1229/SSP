# R-v0.2.1 Fault Recovery PoC 計画

## 目的
R-v0.2（Fault Recovery Manager）で導入された SelfHealingDaemon・StateResync・AlertDispatcher・recovery 系 API を対象に、障害注入と連続稼働によって「検知→再起動→状態復元→通知」のフローが実運用レベルで機能するかを検証します。PoC で得られた数値を恒久仕様（Retry 回数、通知ルール、監視設定）に反映し、R-v0.2 の完成度を上げるのが狙いです。

## KPI（合格ライン）
| 指標 | 合格ライン |
| --- | --- |
| 自動復旧成功率 | 95%以上（FailureInjector 実行中） |
| State Resync 成功率 | 90%以上（DB/Redis 停止後の復元） |
| 平均復旧時間 | 60秒以内（クラッシュ〜正常化） |
| AlertDispatcher の通知漏れ | 0件 |

## シナリオとコマンド

### シナリオA：単一モジュールのクラッシュ
```powershell
python tools\r_v0_2_failure_injector.py --scenario single-module --iterations 3 --pause 2 --base-url http://127.0.0.1:8000
```
- `/api/system/health` → `/api/recovery/restart` → `/api/system/metrics` を順番に呼び、SelfHealingDaemon の再起動と AlertDispatcher の通知動作を観察。
- 再起動ログ（`logs/r_v0_2_1_poc.jsonl`）で各リクエストのステータスを記録し、失敗件数と復旧時間を集計。

### シナリオB：DB/Redis の一時停止
```powershell
python tools\r_v0_2_failure_injector.py --scenario db-redis-down --iterations 2 --pause 3 --base-url http://127.0.0.1:8000
```
- `/api/recovery/state_resync` で State Resync を強制実行しつつ、`/api/system/health` と `/api/system/metrics` への影響を確認。
- Redis/PostgreSQL 停止時の SessionLog 欠損率と復元成功率を計測。

### シナリオC：複数モジュール連鎖クラッシュ
```powershell
python tools\r_v0_2_supervisor_scenario_runner.py --duration 120 --interval 5 --base-url http://127.0.0.1:8000
```
- `/api/system/health` と `/api/recovery/state_resync` を定期ポーリングし、複数モジュールのクラッシュ/再起動回数・平均復旧時間を記録。
- AlertDispatcher が致命的障害をすべて通知し、通知漏れがないかを確認。

## 実行フロー
1. バックエンドを起動：`python -m uvicorn backend.main:app --reload`  
2. シナリオA〜C を順番に実行し、各コマンドの出力と `/logs/r_v0_2_1_poc.jsonl` のログを保存。  
3. `backend/tests/test_r_v0_2_fault_recovery_poc.py` で PoC ロジックのユニットテストを実行。  
4. `frontend/app/analysis/r_v0_2_resilience/page.tsx` で KPI（復旧回数・時間・通知）を確認。  
5. `docs/operations/r_v0_2_1_poc_report.md` に実測値と恒久仕様案を記入。

## 合格基準
- すべてのシナリオで KPI（成功率・復旧時間・通知漏れ）が合格ラインを満たすこと。  
- PoC結果に基づき、R-v0.2 の恒久仕様（Retry 3 回・Alert 4 回失敗で通知・State Resync 成功基準）を言語化すること。  
- `R-v0.2.1_PoC` を `progress=100` / `status=✅` に更新できるだけの証跡（ログ・報告）が揃うこと。
