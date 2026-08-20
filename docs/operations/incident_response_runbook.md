# インシデント対応ハンドブック（Stage Pipeline）

## 目的と適用範囲
- 対象: `modules/stage_director.py` を中心としたステージ再生パイプライン（TTS + OSC）
- ゴール: 影響範囲を特定し、再生を安全に再開するまでの手順を標準化する

## 監視・検知
- 構造化ログ: `logs/ssp_log_json.log`（`step`, `status`, `duration_ms`, `items`, `error` など）を確認
- 重要イベント:
  - `timeline_load`, `event_execute`, `event_complete`, `checkpoint_*`, `timeline_complete`
- アラートの目安:
  - `event_execute` が `failed`/`retrying` で連続発生
  - `checkpoint_save` に `last_error` が残ったまま更新されない

## 初動対応（5分以内）
1. 事象確認: 直近の構造化ログを検索し、`error` と `event_index` を特定
2. 影響範囲: `logs/stage_checkpoints/<timeline>.json` の `next_event_index` を確認し未処理イベントを把握
3. 安全化: 影響がある OSC/TTS 出力を一時停止（`/api/stage/stop`）し、再生要求を抑止

## 復旧手順（チェックポイント活用）
1. **再実行前準備**
   - エラー原因（ネットワーク断/音声生成失敗など）を解消
   - `logs/stage_checkpoints/<timeline>.json` に `next_event_index` が設定されていることを確認
2. **部分再処理/リトライ**
   - 再度 `/api/stage/play` を呼び出すと、`next_event_index` から再開
   - 自動リトライは各イベントで最大 `max_retries` 回（デフォルト2回）実施
3. **手動再実行（必要時）**
   - チェックポイントをリセットして最初から再生: 対象ファイルを削除し `/api/stage/play`
   - 進行中に停止したい場合: `/api/stage/stop` を呼び出し、再度 `/api/stage/play`
4. **確認**
   - `timeline_complete` ログが `status=ok` で出力されていることを確認
   - ダッシュボード/クライアントへのステータス通知 (`status=stopped`) が届いているかを確認

## FAQ（想定問答）
- **Q: どこまで処理が進んでいるか知りたい**
  - A: `logs/stage_checkpoints/<timeline>.json` の `next_event_index` が次に処理するイベント番号です。
- **Q: 自動リトライ後も失敗する場合は？**
  - A: エラーログの `error` を確認し、外部依存（TTS/OSC サービス、ネットワーク）を復旧させてから `/api/stage/play` を再実行してください。
- **Q: 部分的に再生を巻き戻したい**
  - A: チェックポイントを編集し `next_event_index` を任意の番号に変更することで開始位置を調整できます。
- **Q: ログを追跡しやすくする方法は？**
  - A: JSON ログを `jq` やダッシュボードに取り込み、`step`/`status`/`event_index` でフィルタしてください。

## 事後対応
- 原因と対策を運用記録に残す（失敗したイベント、エラーメッセージ、復旧手順）
- 再発防止策を検討し、必要に応じてリトライ回数やタイムアウトを調整
