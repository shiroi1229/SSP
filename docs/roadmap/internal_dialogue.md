# Internal Dialogue Engine (A-v3.5) Runbook

## コンポーネント

- `modules/internal_dialogue.py`: Awareness snapshot からペルソナ対話を生成し、`internal_dialogues` テーブルへ保存。
- `backend/api/internal_dialogue.py`: `/api/internal-dialogue/logs` と `/api/internal-dialogue/generate` を提供。
- `frontend/components/dashboard/InternalDialogueFeed.tsx`: ダッシュボードで内的対話フィードを表示。
- `orchestrator/scheduler.py`: 30 分ごとに `generate_internal_dialogue` をジョブ実行。

## 手動トリガ

```powershell
python -c "from modules.internal_dialogue import generate_internal_dialogue; print(generate_internal_dialogue())"
```

もしくは API で:

```bash
curl -X POST http://localhost:8000/api/internal-dialogue/generate
```

## ロードマップ更新

1. 対話エンジンが稼働し、ダッシュボードに表示されることを確認。
2. `PATCH /api/roadmap/A-v3.5` で progress を 10% 程度に更新（UI からでも可）。
3. `python tools/update_system_roadmap.py` → `git commit docs/roadmap/system_roadmap*.json` → push。
