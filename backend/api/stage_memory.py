# path: backend/api/stage_memory.py
# version: UI-v1.2
from fastapi import APIRouter
from modules.stage_memory import StageMemoryManager

router = APIRouter()
manager = StageMemoryManager()

@router.post("/api/stage/memory/sync")
async def sync_stage_memory():
    """Trigger synchronization of stage logs to RAG memory."""
    manager.sync_stage_memories()
    return {"status": "synced"}

@router.get("/api/stage/memory/search")
async def search_stage_memory(query: str):
    """Query past stage memories."""
    result = manager.query_stage_knowledge(query)
    return {"result": result}
