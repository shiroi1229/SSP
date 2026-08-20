# R-v0.3.1 Contracted I/O Model 恒久仕様

## 目的
R-v0.3（Contracted I/O Model）で PoC した診断フロー（ログ収集→DiagnosticEngine→AlertManager→InsightLinker）を、**24/7 で稼働する恒久仕様**に昇格させる。PoCで得た `logs/r_v0_3_poc.jsonl` の数値を最低ラインとし、以下の要件を「運用中の品質保証」として継続的に担保する。

## 恒久仕様の要件
| 項目 | 恒久基準 | 計測方法 |
| --- | --- | --- |
| エラー検出精度（カテゴリ別） | 主要カテゴリ（I/O / Dependency / Logic / Resource）を 95% 以上検出 | DiagnosticEngine の `findings` に `category` が含まれ、PoCログと比較した差分が 5% 未満 |
| Alert 通知成功率 | 99% 以上（スラック/メール/etc.） | AlertManager の dispatch_alert が `status: success` を出す割合 |
| Insight 連携マッチ | `matched_findings` ≥ 1 かつ 90%以上 | InsightReport との `matched_findings` 比率を追跡 |
| 遅延 | `/api/system/diagnose` の応答 ≤ 1 秒 | PoCログの `duration_ms` を 1000ms 未満に固定 |
| PoC ログ蓄積 | 1日最低 1 行（CI で夜間実行） | `logs/r_v0_3_poc.jsonl` に timestamped エントリが存在 |

## 実装アクション
1. **診断エンジン強化**  
   - `modules/diagnostic_engine.py` に複数ログソース（SessionLog / application.log / orchestrator）の読み込みを追加。  
   - カテゴリ判定の閾値を config/thresholds.yaml に抽象化し、PoC との差分を自動で比較する。

2. **Alert Reliability**  
   - `modules/alert_manager.py`／`modules/alert_dispatcher.py` に retry/backoff を導入。  
   - 失敗時は `logs/alert_dispatcher.log` に記録し、KPI を Prometheus で expose（exposure via `/metrics/alerts`）。

3. **Insight Monitoring**  
   - `/api/system/diagnose` に `insight` サブフィールドを追加し、`matched_findings`・`insight_highlights` を返す。  
   - `frontend/app/diagnostic/page.tsx` に「PoC→本番」での状態差分（PoC timestamp / latest run）を表示。

4. **運用 PoC の自動化**
   - PoC runner（`tools/r_v0_3_diagnostic_poc_runner.py`）を CI（夜間）で走らせ、`logs/r_v0_3_poc.jsonl` を日次 rotate しながら `insight_history` のスナップショットを保存。  
   - PoC ログが 7 日以上存在しなければ自動アラート（`/api/system/diagnose` から `alert` に injection）。  

5. **恒久監視と運用手順**
   - `docs/operations/r_v0_3_poc_report.md` の末尾に「恒久運用チェックリスト」（例：Alert config 更新、CI の PoC 実行、Log retention の確認）を追加。  
   - `config/alert_targets.yaml` に本番 Slack/Email ターゲットを投入した上で、通知テストを毎週実行。
   - `tools/r_v0_3_poc_health_check.py` を Cron/スケジューラ上で定期実行し、`logs/r_v0_3_poc.jsonl` のエントリ数と PoC runner の最新 run timestamp を監視する。
   - `backend/api/system/diagnose.py` の `/diagnose/health` から summary を返し、`frontend/app/analysis/r_v0_3_diagnostic/page.tsx` にステータスを表示。

## 評価 / 次のステップ
1. **PoC runner の定期実行**  
   - `tools/r_v0_3_diagnostic_poc_runner.py --mode http --scenario baseline --iterations 1` を夜間（例: `cron: 0 3 * * *`）で動かし、`logs/r_v0_3_poc.jsonl` と `logs/r_v0_3_poc_summary.json` を更新。  
   - 実行後は `tools/r_v0_3_poc_health_check.py` を同じジョブで続けて呼び出し、ログ件数と最新 run timestamp を検証。Exit code 0 のままログに「PoC log entries: N」と出るようにしておく。  
   - サンプルcron（Linux/WSL等）:  
     ```cron
     0 3 * * * cd /path/to/repo && /usr/bin/env python tools/r_v0_3_diagnostic_poc_runner.py --mode http --scenario baseline --iterations 1 && /usr/bin/env python tools/r_v0_3_poc_health_check.py
     ```  
   - GitHub Actions 例: `workflow` で `python tools/r_v0_3_diagnostic_poc_runner.py ...` + health check を順次実行。
2. **結果を可視化**  
   - `frontend/app/analysis/r_v0_3_diagnostic/page.tsx` は先ほど Health API を表示しているので、KPI の劣化（Alert success < 99% など）があれば即座にページ上に反映される。  
   - `docs/operations/r_v0_3_poc_report.md` に日次・週次レポート欄を追加して、PoC run ID、`insight_matches`、`alert_attempts`、`duration_ms` を必ず埋める。
3. **ロードマップでの追跡**  
   - `R-v0.3` を完了ステータスとし、`R-v0.3.1` で「恒久監視（PoC runner＋Health check）」を継続的に追跡。  
   - PoC runner による Alert success が 99% を下回った際には AlertManager の retryパラメータ、diagnostic_engine の keyword list、InsightLinker の Insight Rate を検討する「再調整」の runbook を起動する。
