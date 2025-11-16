from fastapi import APIRouter, HTTPException, Query

from orchestrator import insight_monitor as insight_module

router = APIRouter(prefix="/causal", tags=["Causal"])


@router.get("/insight")
def causal_insight(sample_size: int = Query(50, ge=10, le=200)):
    monitor = getattr(insight_module, "global_insight_monitor", None)
    if monitor is None:
        raise HTTPException(status_code=503, detail="Insight monitor not initialized.")
    return monitor.compute_causal_integrity(sample_size)
