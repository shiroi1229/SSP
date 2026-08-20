from fastapi import APIRouter, HTTPException, Query

from modules.causal_trace import trace_event

router = APIRouter(prefix="/causal", tags=["Causal"])


@router.get("/trace")
def trace(event_id: str = Query(..., description="Causal event ID"), depth: int = Query(3, ge=1, le=5)):
    result = trace_event(event_id, depth)
    if not result["nodes"]:
        raise HTTPException(status_code=404, detail="Event not found.")
    return result
