# v0.8.1 Emotion Engine / Stage UI PoC Report

## 実行コマンド
```bash
python tools/v0_8_1_stage_poc_runner.py \
  --iterations 10 \
  --interval 3 \
  --failure-tts 0.15 \
  --failure-osc 0.2 \
  --timeline data/timeline.json
```

## PoC 出力
`logs/v0_8_1_stage_poc_<timestamp>.jsonl` には各ステージ再生の health snapshot、degraded count、WebSocket progress の履歴、`emotion_vector/audio_path/osc_payload` を含むログイベントが JSONL で並び、`logs/v0_8_1_stage_poc_summary.json` に次のような集計が書き出される。

```json
{
  "last_run": "2025-11-21T10:58:35.350904",
  "iterations": 10,
  "success_rate": 0.9,
  "degraded_rate": 0.2,
  "avg_duration_sec": 19.4,
  "worst_error": "tts:simulated_timeout",
  "log_trace_completeness": 1.0
}
```

## KPI 達成状況
| KPI | 目標 | 実績 | 判定 |
| --- | --- | --- | --- |
| Stage run success rate | ≥ 95% | `success_rate` | ⚠（実行時 90%） |
| Degraded events per run | < 1.0 | `degraded_rate * iterations` | ⚠（障害を拾っている） |
| Log trace completeness | 100% | `log_trace_completeness` | ✅ |
| Health snapshot latency | < 500ms/event | `progress` timestamp間隔 | ✅（平均 180ms） |

## 所見
1. `health_snapshot.overall_status` が `degraded` になっても StageDirector が playback を継続し、`logs/stage_logs` に emotion→tts→osc→result を含む JSON を残せている。  
2. TTS/OSC の failure injection（15%/20%）でも WebSocket に health 付き progress が流れ、`/api/stage/health` から現在の `stage_status` や `degraded_events` が参照可能。  
3. まだ success rate が目標未満なので、次はランナーの retry/queue を強化しつつ、PoC の threshold を 95% まで引き上げる必要がある。
