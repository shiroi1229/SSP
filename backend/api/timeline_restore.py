from fastapi import APIRouter, Query

from modules.timeline_rebuilder import rebuilder

router = APIRouter(prefix="/timeline", tags=["Timeline"])


@router.get("/restore")
def restore_timeline(limit: int = Query(50, ge=10, le=200)):
    return rebuilder.rebuild_timeline(limit=limit)
