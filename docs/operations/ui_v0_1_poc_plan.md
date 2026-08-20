# UI-v0.1 PoC 計画

## 背景
UI-v0.1（Basic WebUI） は `frontend/app/chat` を中心に、ユーザー入力 → /api/chat → RAG検索 → UI表示というシンプルなチャット輪を構成します。  
PoC: `UI-v0.1_PoC` では、このチャットフローが実際のトラフィック下でも安定して動くこと、RAGのソース提示・評価機能が正常に動作すること、及び UI での応答可視化が想定どおり表示されることを確認します。

## 目的
- `/api/chat` のレスポンス品質と RAG リファレンスの整合性をリアルユーザーリクエストで検証する。  
- `frontend/app/chat/page.tsx` の `ChatPanel` → `useChat` → `useEvaluation` ルートがエラーなく動くことを確認する。  
- PoCスクリプトが返す応答と UI での表示パターンが一致していることをフローで確認し、`docs/operations/ui_v0_1_poc_report.md` に実測を記録する。  
- 予期せぬエラー（500/timeout/評価失敗）に対しては `logs/ui_v0_1_poc.jsonl` に記録し、今後の調整に使う。

## KPI
| 指標 | 合格ライン |
| --- | --- |
| `/api/chat` 応答ステータス | 200（全リクエスト） |
| RAG references 有無 | 100%（応答に `references` が含まれている） |
| 評価登録成功率 | 100%（`useEvaluation` 経由で保存される） |
| UI 表示整合（ChatPanel） | 自動完了（メッセージ・references が画面描画） |

## 実行手順
1. **PoCツールを起動**  
   ```powershell
   python tools\ui_v0_1_poc_runner.py --base-url http://127.0.0.1:8000 --iterations 5 --pause 1
   ```  
   → `/api/chat` へランダムなプロンプトを送り、`references` と `evaluation` 回収を同時に検証。レスポンスと UI 連携をログに記録（`logs/ui_v0_1_poc.jsonl`）。

2. **UI（Next.js） で確認**  
   ```powershell
   cd frontend
   npm run dev
   ```  
   → ブラウザ `http://localhost:3000/chat` にアクセスし、PoCツールと同様のプロンプトが ChatPanel に表示されること・RAGInsightPanel に references が表示されることを目視確認。

3. **テスト**  
   ```powershell
   python -m pytest backend/tests/test_ui_v0_1_poc.py
   ```  
   → PoCランナーの内部ロジック（requests が 200 返すこと、references 取得）をモックで検証。

4. **報告書**  
   - `docs/operations/ui_v0_1_poc_report.md` に実測値（ステータス/ references）・UI観察・恒久仕様（応答時間/評価結果保存）を記録。  

5. **完了判定**  
   - KPI をすべて満たしたら `UI-v0.1_PoC` の `progress=100` / `status=✅` に更新し、PoCが完了したことをロードマップ/DBに反映。
