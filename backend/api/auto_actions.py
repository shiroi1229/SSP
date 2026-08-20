from fastapi import APIRouter, Query

from modules.auto_action_log import read_actions
from modules.auto_action_analyzer import compute_action_stats

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])

@router.get("/actions")
def get_auto_actions(limit: int = Query(50, ge=10, le=200)):
    entries = read_actions(limit)
    stats = compute_action_stats(limit)
    return {"entries": entries, "stats": stats}
