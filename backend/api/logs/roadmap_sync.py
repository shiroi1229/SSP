from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import os

router = APIRouter(prefix="/api/logs")

@router.get("/roadmap_sync")
async def get_roadmap_sync_log():
    """
    Returns the content of the roadmap_sync.log file.
    """
    log_path = "logs/roadmap_sync.log"
    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            return PlainTextResponse(content)
        else:
            raise HTTPException(status_code=404, detail="Roadmap sync log not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
