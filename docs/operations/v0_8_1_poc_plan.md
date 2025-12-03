# v0.8.1 Emotion Engine / Stage UI PoC Plan

## Purpose
v0.8.1 で求められる Emotion Engine / Stage UI の恒久運用性（障害混入後も進行が止まらないこと・emotion → tts → osc → result のログトレースが取れること）を PoC で再現し、クラッシュ・遅延・ログ欠落のコンディション下で全体の堅牢性が維持できるかを検証する。

## Execution environment
1. `uvicorn backend.main:app --reload` で Stage API + WebSocket を起動し、`http://127.0.0.1:8000` をターゲットにする。
2. `data/timeline.json`（スクリプト未作成なら StageController がダミー台本を埋める）をステージ再生の input とする。
3. `tools/v0_8_1_stage_poc_runner.py` を実行し、`logs/v0_8_1_stage_poc_*.jsonl` + `logs/v0_8_1_stage_poc_summary.json` を出力して障害ログを残す。

## Scenarios
- `baseline`: ステージを連続再生し、OSC/TTS すべて success（failure0%）で安定性とログ一貫性を確認。
- `tts_degraded`: 合成リクエストをランダムに失敗（例: 15%）させて、StageDirector が WebSocket/ログに「degraded」として health snapshot を含め、次のイベントへフェイルオーバーする挙動を確認。
- `osc_failure`: OSC 送信をランダム落ち（例: 20%）させ、重複ログ・health_summary、progress WebSocket で再送／エラー表示が出ることを確認。
- `long_run`: 同じ状態で 30 分相当の連続イベント（iteration を増やす）を実行し、emotion→tts→osc→result の記録と `memory_store` のアーカイブが破綻しないことを観察。

## Metrics
| KPI | Goal | Source |
| --- | --- | --- |
| Stage run success rate | ≥ 95% | JSONL `status` field (`ok`/`degraded`) |
| Degraded events per run | < 1.0 | `health_snapshot.overall_status` で `degraded` を含む件数 |
| Log trace completeness | 100% | 各 run record の `emotion_vector` / `audio_path` / `osc_payload` フィールドが null でない割合 |
| Health snapshot latency | < 500ms between events | `health_snapshot.timestamp` 差分 |

## PoC recipe
1. 以下のように runner を起動し、TTS/OSC の失敗率や iteration、interval を制御する。
```bash
python tools/v0_8_1_stage_poc_runner.py \
  --iterations 8 \
  --interval 2 \
  --failure-tts 0.15 \
  --failure-osc 0.2 \
  --timeline data/timeline.json
```
2. runner が `logs/v0_8_1_stage_poc_<timestamp>.jsonl` へ各 run の health summary・timestamps・error を JSONL 格納し、集約は `logs/v0_8_1_stage_poc_summary.json` にまとめる。
3. `docs/operations/v0_8_1_poc_report.md` で summary JSON を引用し、成功率・レイテンシ・ログ一貫性・障害からの復帰動作を記述する。
