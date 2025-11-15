from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modules.distributed_recovery_manager import manager

router = APIRouter()


@router.get("/robustness/distributed-recovery")
def get_recovery_state():
    return manager.get_state()


@router.post("/robustness/distributed-recovery/promote")
def promote_standby(payload: dict):
    standby = payload.get("node")
    if not standby:
        raise HTTPException(status_code=400, detail="node is required")
    try:
        result = manager.promote(standby)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result


@router.post("/robustness/distributed-recovery/status")
def update_node_status(payload: dict):
    name = payload.get("node")
    status = payload.get("status")
    if not name or not status:
        raise HTTPException(status_code=400, detail="node and status are required")
    try:
        result = manager.toggle_status(name, status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result
