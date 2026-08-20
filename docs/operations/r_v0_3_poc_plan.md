# R-v0.3 Diagnostic PoC 計画

## PoC の目的
R-v0.3 の診断エンジン + アラートマネージャ + Insight 連携が「ログから異常を検出し、原因・アラート・改善提案を手早く返せる」状態にあるかを確認します。同時に `/api/system/diagnose` を通じて UI にバッキングデータが出力され、実装した Alert/Insight レイヤが正しく連携していることを実証します。

## KPI（合格基準）
| 評価項目 | 目標値 | 検証方法 |
| --- | --- | --- |
| エラー検出遅延 | 1 秒以内 | PoC スクリプトの `diagnose` 実行ログ（duration_ms） |
| 主要カテゴリの検出精度 | 3 種類（I/O, Dependency, Logic）に対し最低 1 件ずつ検出 | `findings` 数と `category` を logs/r_v0_3_poc.jsonl で確認 |
| Alert ディスパッチ試行 | 1 回以上 | `alert_status` が `skipped`/`failed` ではなく `success` もしくは `failed` で通知済みと判断 |
| Insight 連携 | `matched_findings` > 0 | `insight` フィールドの値を確認 |

## 実行コマンド
### ① ベースライン診断
```powershell
python tools/r_v0_3_diagnostic_poc_runner.py --scenario baseline --mode http --iterations 1 --pause 1
```
- `/api/system/diagnose` を呼び出して診断スタック全体が動作するか確認。ログを追記することで I/O/Dependency/Logic のキーワードを検出させる。  
- 実行後、`logs/r_v0_3_poc.jsonl` に `total_findings` と `alert_attempts` の値が記録される。

### ② Insight 同期サイクル
```powershell
python tools/r_v0_3_diagnostic_poc_runner.py --scenario insight_cycle --mode http --iterations 2 --pause 0.3
```
- Insight Linker のレスポンスに `matched_findings` が含まれること、2 回連続で診断結果に変化があることを見届ける。

### ③ UI で確認
1. `npm run dev`（または `next dev`）でフロントエンドを起動。  
2. `http://localhost:3000/analysis/r_v0_3_diagnostic` にアクセスし、最新の診断レポート・Alert 概要・Insight 概要が表示されることを確認。  
3. PoC ログと照らし合わせ、表示されたステータスが `logs/r_v0_3_poc.jsonl` の `alert_status`/`findings` に一致するかを見る。

## 手順まとめ
1. `python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` を起動。  
2. `config/alert_targets.yaml` の `url` はテスト用に `http://localhost` などに変更するか、`alert_targets` を空にして外部通信を防ぐ。  
3. 上記コマンドで PoC スクリプトを実行し、`logs/r_v0_3_poc.jsonl` に記録された `total_findings/alert_attempts` を確認。  
4. `frontend/app/analysis/r_v0_3_diagnostic/page.tsx` から UI を参照し、Alert メッセージ・Insight の存在を目視で確認。  
5. `docs/operations/r_v0_3_poc_report.md` に実測値を記入し、判断と恒久仕様（Retry 回数・Alert しきい値など）をまとめる。

## 記録先
- PoC ログ：`logs/r_v0_3_poc.jsonl`（1 行につき 1 シナリオの集計データ）  
- 診断対象ログ：`logs/feedback_loop.log`（PoC 中に挿入されたエラー文）  
- 評価レポート：`docs/operations/r_v0_3_poc_report.md`
