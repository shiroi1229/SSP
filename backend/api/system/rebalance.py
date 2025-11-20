"""System rebalance API for R-v0.4."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.modules.load_balancer import load_balancer_service
from backend.modules.task_scheduler import scheduler
from modules.log_manager import log_manager


class RebalanceRequest(BaseModel):
    modes: List[Dict[str, object]] | None = None
    task_priorities: List[Dict[str, object]] | None = None


router = APIRouter(tags=["System"], prefix="/system")


@router.post("/rebalance")
def rebalance(request: RebalanceRequest):
    """Update rebalance modes and adjust scheduler priorities."""
    response: Dict[str, object] = {}
    if request.modes:
        state = load_balancer_service.update_modes(request.modes)
        response["balance"] = state
    if request.task_priorities:
        scheduler.update_tasks([{"name": item.get("name"), "priority": item.get("priority", 5)} for item in request.task_priorities if item.get("name")])
        response["schedule"] = scheduler.peek_schedule()
    if not response:
        raise HTTPException(status_code=400, detail="modes or task_priorities required")
    log_manager.info("[SystemRebalance] Rebalance request processed.")
    return response
