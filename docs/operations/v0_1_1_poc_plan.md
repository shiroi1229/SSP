# MVP Core Metrics PoC計画 (v0.1.1)

## 目的
- v0.1.1で追加した5つのKPI（平均応答時間・成功率・再生成成功率・ログ損失率・スコア5割合）が、実トラフィックを通じて信頼できる数値として観測できることを検証する。
- /api/metrics/v0_1 に返ってくる値と、SessionLog などの生データ／人間の体感に乖離がないかを確認する。

## 評価指標と計測ポイント
1. 平均応答時間: SessionLog.response_time_ms を1秒単位で集計。1.5秒以内が望ましい。
2. 成功率: status_code が 200〜399 のリクエスト割合。
3. 再生成成功率: 再生成フラグ（regeneration_attempts > 0）を立てた上で、ステータス 2xx が返った割合。
4. ログ損失率: metrics_logger が log_persist_failed=1 をセットした件数の比率。
5. スコア5割合: evaluation_score が 5 の件数の割合。

## シナリオ設計
1. `tools/v0_1_1_poc_scenario_runner.py` を使い、/api/chat に20〜50リクエストを流す。デフォルトでは5件ごとに `regeneration=true` を渡す。
2. 各リクエストで `Prompt` をランダムに選択し、平均応答時間 ~0.5s のインターバルを空ける。
3. すべてのリクエストを `SessionLog` に記録し、status_code・response_time_ms・regeneration_*・log_persist_failed を含める。
4. シナリオ実行後に `/api/metrics/v0_1/summary` および `/api/metrics/v0_1/timeseries?hours=2` を叩き、PoC対象期間の値を記録する。

## 自動テスト
- `backend/tests/test_metrics_v0_1_poc.py` で、固定データに対して summary/timeseries の結果が期待値と一致すること（サンプル数・成功率・再生成成功率など）を確認する。これにより API の集計ロジックが壊れていないことを保証する。

## 実施フロー
1. Postgres 上の `session_logs` テーブルに新しいカラム（status_code / response_time_ms / log_persist_failed / regeneration_*）が追加されていることを確認。
2. `tools/v0_1_1_poc_scenario_runner.py` を起動してトラフィックを発生させる。
3. `/api/metrics/v0_1/summary` を取得し、ログと突合して CPU/response_time の整合性を確認。
4. `docs/operations/v0_1_1_poc_report.md` に記録し、差分や気づきを記載する。

## 合格基準
- metrics API の値と、サンプルログ（手動集計）の差が ±10% 以内であること。
- 再生成成功率の計算が `regeneration_success` を真としたときに 0〜1 の範囲で安定していること。
- PoCレポートに記録された値と、ダッシュボードの表示（frontend）に乖離がない状態。
- テスト `backend/tests/test_metrics_v0_1_poc.py` が CI で通ること。
