from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/api", tags=["Logs"])

@router.get("/logs/recent")
def get_recent_logs():
    log_file_path = Path("./logs/introspection_trace.log")
    logs = []
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        # JSON形式でない行はスキップまたはエラーログ
                        pass
        except Exception as e:
            # ファイル読み込みエラー
            pass
    return {"logs": logs}