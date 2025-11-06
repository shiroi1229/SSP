# path: backend/api/logs/recent.py
# version: v0.8
# 概要: ローカルログを読み込み、最新の数十行をJSONで返す

from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter()

@router.get("/api/logs/recent")
async def recent_logs():
    log_path = Path("logs/feedback_loop.log")
    if not log_path.exists():
        return {"logs": []}
    lines = log_path.read_text(encoding="utf-8").splitlines()[-50:]
    logs = [{"timestamp": "", "message": l} for l in lines]
    return {"logs": logs}
