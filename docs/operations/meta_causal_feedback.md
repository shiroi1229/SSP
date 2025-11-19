# Meta-Causal Feedback System (R-v0.9) 運用ガイド

## フェーズ概要
- 目的: Insight Engine・Bias Detector・Self Optimizer を一体化し、因果データの偏向を検知→最適化→自動対策まで閉ループ化。
- 成果物: `modules/meta_causal_feedback.py` による自己分析、`bias_history`/`auto_actions`/`optimizer_history` ログ、可視化 UI (`/meta_causal`)。
- ※2025-11-16 時点で UI には Meta レポートカード (insight narrative + 推奨アクション) を追加済み。

## バックエンド構成
| モジュール | 役割 |
| --- | --- |
| `modules/meta_causal_feedback.run_feedback` | 偏向検知→Self-Optimizer→Auto Action 記録まで実行。 |
| `modules/bias_history.py` | 長期バイアス蓄積と平均化、アラート生成。 |
| `modules/auto_action_log.py` / `modules/auto_action_analyzer.py` | Insightの自動対策ログ保存／成功率集計。 |
| `modules/optimizer_history.py` | Self-Optimizer のパラメータ/結果履歴。 |
| `modules/meta_causal_report.py` | 上記データを集約し説明レポート (`/api/meta_causal/report`) を生成。 |

### API 一覧
- `GET /api/meta_causal/feedback` – 因果ループ構造 (FeedbackLoopGraph用)。
- `POST /api/meta_causal/feedback/run` – Meta-Causal フィードバック実行。
- `GET /api/meta_causal/bias` / `/bias/history` – 偏向スナップショットと長期傾向。
- `GET /api/meta_causal/actions` – 自動対策ログ＋成功率。
- `GET /api/meta_causal/optimizer/history` – Self-Optimizer 履歴。
- `GET /api/meta_causal/report` – Insight Narrative + 推奨アクション（新規）。

## ログ/データ保存先
- `logs/bias_history.jsonl` – `detect_bias` の結果を逐次追記。
- `logs/auto_actions.jsonl` – Insight / Meta-Causal の自動対策履歴。
- `logs/meta_optimizer_history.jsonl` – Self-Optimizer 実行ログ。
- これらは Meta レポート生成や `/meta_causal` UI で利用。

## 運用手順
1. **偏向チェック & 自己再設計**
   ```bash
   curl -X POST http://localhost:8000/api/meta_causal/feedback/run
   ```
   - 成功すると `logs/bias_history.jsonl` と `logs/meta_optimizer_history.jsonl` に追記される。
2. **Insight Narrative 確認**
   ```bash
   curl http://localhost:8000/api/meta_causal/report | jq
   ```
   - `summary` と `recommendations` の内容が `/meta_causal` ページのカードにも表示される。
3. **自動対策ログを見る**
   ```bash
   curl http://localhost:8000/api/meta_causal/actions
   ```
   - `stats` で各アクションタイプの成功率を把握。`should_execute` 判定は Insight Monitor 内で参照される。
4. **長期偏向のモニタリング**
   ```bash
   curl http://localhost:8000/api/meta_causal/bias/history
   ```
   - `alerts` にしきい値超過や急激な変動がまとめられる。

## ダッシュボード
- `/meta_causal` に以下を表示:
  - Insightメトリクス (ノード数/成功率/自動対策状態)。
  - Long-term Bias timeline (`BiasHistoryTimeline`)。
  - Optimizerパネル。
  - Auto Actionログ＋成功率カード。
  - **Meta Reportカード (今回追加)**: `/api/meta_causal/report` の `summary`/`highlights`/`recommendations` をそのまま表示し、最新自動対策の結果も添える。

## テスト
- 主要テスト: `python -m pytest backend/tests/test_meta_causal_feedback.py`
  - 新たに `/api/meta_causal/report` の構造を検証するテストを追加済み。
- UI 側は Next.js で動的に SWR fetch。型は `frontend/app/meta_causal/page.tsx` 内で定義。

## ロードマップ反映
- DB: `roadmap_items` の `R-v0.9 Meta-Causal Feedback System` を `status=✅`, `progress=100`, `documentationLink='docs/operations/meta_causal_feedback.md'` に更新。
- ドキュメント: `dump_roadmap_to_file.py` → `tools/update_system_roadmap.py` を実行し、GitHub 表示向け JSON を再生成。

これで R-v0.9 の残要件（Insight 自動対策の評価、説明レポート生成、UI 可視化強化）が完了し、次段階 (R-v1.0) に進めます。
