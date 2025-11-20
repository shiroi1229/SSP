# R-v0.1.1 Resilience PoC 計画

## 背景
R-v0.1（Core Stability Framework）はロードマップ上「止まらないAI」の土台を整えた段階ですが、実運用を想定した障害にも耐える「恒久仕様」になっているかを検証しきれていません。  
この PoC では RetryManager・Logger・ConfigLoader・Supervisor を中心に、以下のような障害シナリオで「自動復旧」「ログ欠損ゼロ」「手動介入ゼロ」を目指します。

## PoC の目的
- 障害が起きても system_health・metrics・retry が 3 回以内に再起動できる安定性を確認する  
- ログは欠損せず、再起動後 30 秒以内に回復すること（ログ欠損率 < 1%）  
- 手動介入（設定変更や再起動）が発生しないよう、Supervisor / RetryManager による自動復旧を確認する  
- この結果をもとに、R-v0.1 の恒久仕様（タイムアウト, リトライ回数, アラート閾値）を固める

## シナリオと追跡項目

### 1. 計画 (docs/operations/r_v0_1_1_poc_plan.md)
- PoC 期間：2025-02-25 〜 2025-03-05
- 想定障害
  - API 内部エラー・例外（/api/system/health など）
  - PostgreSQL / Redis の一時的応答停止
  - 環境変数の書き換え・ConfigLoader の警告
  - Supervisor 対象プロセスの人工クラッシュ
- 評価指標
  - 24 時間のうち致命的停止回数（目標 0 件）
  - 障害発生から復旧完了までの平均時間（30 秒以下）
  - ログ欠損率（1% 未満）
  - 手動介入件数（0 〜 極少）

### 2. 実行 (tools/r_v0_1_failure_injector.py, tools/r_v0_1_supervisor_stress_runner.py)
- `failure_injector` で指定エンドポイントに対して 5 種類の異常リクエスト（無効ペイロード・404 等）を注入し、ログと metrics を確認  
- `supervisor_stress_runner` で Supervisor 管理対象を繰り返しクラッシュさせ、再起動時間とログ欠損の有無を測定  
- 両ツールともログ出力（JSON）を `logs/r_v0_1_1_poc.jsonl` に追記する

### 3. 検証 (backend/tests/test_r_v0_1_resilience_poc.py)
- failure_injector で取得した結果から、各エンドポイントでステータスコード 200/2xx もしくは 5xx を含むが継続運用できることを確認  
- Supervisor stress runner はタイムアウト・再起動時間の記録をチェックし、平均復旧時間が 30 秒未満であることをアサートする  
- `pytest` を使い、FakeSession によるモック検証を行う

### 4. 可視化 (frontend/app/analysis/r_v0_1_resilience/page.tsx)
- PoC 指標（再起動回数・平均復旧時間・ログ欠損・手動介入）をダッシュボード化し、依存 API（/api/system/metrics）と比較  
- ウィンドウごとに metrics が揃っているか、グラフ/カードで確認可能とする

### 5. 報告 (docs/operations/r_v0_1_1_poc_report.md)
- 各指標の実測値と合格ライン、気づき・改善案を記述  
- 必要に応じて恒久仕様（Retry 回数・Supervisor sleep・アラート条件）の改定を提案

## 進捗
- `tools/` スクリプトのログは `reports/r_v0_1_1_poc/` に保存する  
- PoC 終了後、指標を `docs/operations/r_v0_1_1_poc_report.md` に記録し、R-v0.1 恒久仕様に反映
