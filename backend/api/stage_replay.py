# path: backend/api/stage_replay.py
# version: UI-v1.2
"""
API endpoints for replaying and listing recorded stage runs.
"""

from fastapi import APIRouter, HTTPException
from modules.stage_recorder import StageRecorder
import asyncio
import os

router = APIRouter()
recorder = StageRecorder()

@router.get("/api/stage/logs")
async def list_stage_logs():
    """Return available recorded stage logs."""
    return {"logs": recorder.list_logs()}

@router.post("/api/stage/replay")
async def replay_stage_endpoint(log_name: str):
    """Replay a specific recorded stage."""
    # Basic security check to prevent directory traversal
    if ".." in log_name or not log_name.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid log name.")
        
    log_path = os.path.join("logs/stage_runs", log_name)
    
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log file not found.")

    # Run the replay task in the background
    asyncio.create_task(recorder.replay_stage(log_path))
    return {"status": "replaying", "log": log_name}
