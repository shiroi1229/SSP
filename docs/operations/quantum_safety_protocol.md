# Quantum Safety Protocol (R-v0.6) 運用ガイド

## フェーズ概要
- 目的: Distributed Recovery System 上に量子耐性セキュリティ層を追加し、「壊れにくい」から「欺けない」AIへ強化。
- 要素技術: Post-Quantum Cryptography (PQC) 署名、Zero-Knowledge Proof (ZKP)、Insight Engine による信頼スコアリング。
- 主要成果物: `backend/security/` モジュール群、`/api/security/*` エンドポイント、`/security` UI パネル、定期リフレッシュジョブ。

## バックエンド構成
| モジュール | 役割 |
| --- | --- |
| `quantum_cipher.py` | PQC鍵の生成・ローテーション、署名履歴の保持。|
| `integrity_checker.py` | Redis/ログ由来のチャンネル指標からハッシュ/ドリフト/推奨アクションを計算。|
| `zkp_engine.py` | チャンネルごとにZKPライクな証跡を生成し、ネットワーク状態を判定。|
| `insight_integrity.py` | PQC・Integrity・ZKPの指標を統合し、`trust_index` と推奨対応を出力。|
| `refresh_runner.py` `refresh_log.py` | データリフレッシュスクリプトの実行/再試行判定/ログ収集。|

FastAPI ルーター: `backend/api/security.py`
- `GET /api/security/verify`: 量子鍵・Integrity・ZKP・Insight のスナップショットを返却。
- `GET /api/security/refresh-log`: `logs/security_refresh.log` を整形して可視化向けに返却。
- `POST /api/security/refresh-run?dry_run=`: `scripts/refresh_security_sources.py` を起動し、必要に応じて再署名/リフレッシュを実施。

## フロントエンド (`/security`)
- `frontend/components/dashboard/SecurityConsole.tsx` が `SecuritySnapshot` 型を元に UI を構築。
- 量子署名トレース、Integrity チャンネル、ZKP、Insight 推奨、リフレッシュ履歴を一画面で確認可能。
- TypeScript 型は `frontend/types/Security.ts` に集約 (PQC署名/Integrity/ZKP/Insight/ログレスポンス)。

## データリフレッシュ運用
1. 手動実行  
   ```powershell
   python scripts/refresh_security_sources.py --dry-run   # 検証のみ
   python scripts/refresh_security_sources.py             # 本番反映+ログ追記
   ```
2. スケジュール実行 (例: Windows で毎日 03:00 に SYSTEM 権限で実行)  
   ```powershell
   schtasks /create /sc daily /st 03:00 `
       /tn SSP-SecurityRefresh `
       /tr "`"D:\gemini\scripts\run_security_refresh.bat`"" `
       /rl HIGHEST /f /ru SYSTEM
   ```
   - `run_security_refresh.bat` は `C:\Python313\python.exe D:\gemini\scripts\refresh_security_sources.py` を起動。
   - ログは `logs/security_refresh.log` (`refresh_log.read_recent_refresh_entries`) へ追記。
3. `/api/security/refresh-log` で結果と自動再試行（`autoRetry`）を確認。

## チェックリスト
1. `GET /api/security/verify` が `quantum_layer`, `integrity`, `zkp`, `insight` の4階層を返すか。
2. `rekey_event` が出た場合は `recommended_action` に従い PQC 鍵を再発行（`quantum_cipher.rotate_key()`）。
3. `/security` UI で以下を確認:
   - 信頼指数 (`trust_index`) が 0.94 以上か。
   - Integrity チャンネルに `status=rekeying` が残っていないか。
   - リフレッシュ履歴に連続失敗 (`recentFailures`) が無いか。
4. 障害時は `scripts/refresh_security_sources.py --dry-run` で再現 → `POST /api/security/refresh-run` でリカバリ。

## テストと検証
- 単体テスト:  
  ```powershell
  python -m pytest backend/tests/test_security_api.py
  ```
  Quantum署名/ZKP/リフレッシュAPIのレスポンス構造とフェイルケース検知をカバー。
- フロント lint (必要に応じて): `npm run lint`

## ロードマップ反映
- DB: `roadmap_items` の `version='R-v0.6'` を `status='✅'`, `progress=100`, `documentationLink='docs/operations/quantum_safety_protocol.md'` に更新済み。
- ドキュメント: `dump_roadmap_to_file.py` → `tools/update_system_roadmap.py` で `docs/roadmap/*.json` を再生成し、GitHub 表示と整合。

以上で Quantum Safety Protocol (R-v0.6) の残要件（Integrity Checker 可観測化 + UI + 運用手順）が完了です。
