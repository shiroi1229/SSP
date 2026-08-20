# Temporal Recovery Layer (R-v0.7)

Temporal Recovery Layer は Quantum Safety Protocol の通信整合性を前提に、過去のコンテキスト履歴を再走査して「欠損」「改ざん」「未反映」のギャップを検出し、推奨ロールバックを提示するレイヤーです。バックエンド API とフロントエンド UI を組み合わせて、自己履歴の巻き戻しと修復を安全に行います。

## API

### `GET /api/timeline/restore`
- **Query**
  - `limit` (10-200, default 50): 取得する履歴件数
  - `layer` (optional): `short_term` や `long_term` など、特定レイヤーの履歴だけに絞る
- **Response**
  ```json
  {
    "timeline": [
      {
        "timestamp": "2025-11-15T10:00:00",
        "layer": "short_term",
        "status": "missing",
        "note": "short_term.self_analysis",
        "has_snapshot": false,
        "snapshot_path": null
      }
    ],
    "summary": {
      "entries": 42,
      "gaps_detected": 3,
      "needs_rollback": true,
      "recommended_timestamp": "2025-11-15T10:00:00",
      "snapshots_available": 18,
      "layer": "short_term"
    },
    "notice": "No timeline entries found for layer 'long_term'."
  }
  ```
- 推奨ロールバック時刻が存在する場合、`needs_rollback` が `true` になります。

### `POST /api/context/rollback`
- **Body**
  ```json
  {
    "timestamp": "2025-11-15T10:00:00",
    "reason": "timeline-gap-auto"
  }
  ```
- **Response**
  ```json
  {
    "success": true,
    "payload": {
      "restored_at": "2025-11-16T09:12:31.001Z",
      "requested_timestamp": "2025-11-15T10:00:00",
      "reason": "timeline-gap-auto",
      "snapshot": { ... },
      "snapshot_file": "data/context_rollback_snapshot.json"
    },
    "log": {
      "restored_at": "2025-11-16T09:12:31.001Z",
      "requested_timestamp": "2025-11-15T10:00:00",
      "reason": "timeline-gap-auto",
      "snapshot_file": "data/context_rollback_snapshot.json"
    }
  }
  ```
- 実行ログは `logs/context_rollback.jsonl` に追記されるため、Temporal Recovery の監査に使用できます。

## Frontend ( `/timeline` )
- 履歴件数スライダーとレイヤーフィルターで `/api/timeline/restore` を再取得
- 推奨ロールバックがある場合は「Rollback to recommendation」ボタンで `/api/context/rollback` を呼び出し
- Timeline カードでは各イベントのレイヤー・ステータス・スナップショット有無・ファイルパスを表示

## 運用フロー
1. `/timeline` ページでギャップを確認（`needs_rollback` が true の場合）
2. 自動提案が妥当であれば [Rollback] ボタンで `/api/context/rollback`
3. ロールバック結果は `data/context_rollback_snapshot.json` と `logs/context_rollback.jsonl` に保存
4. 再度 `/api/timeline/restore` を実行してギャップが解消されたことを確認

これにより、R-v0.7 で求められる「過去履歴の再演と修復」が UI/API 双方で完結します。
