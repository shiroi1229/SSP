from __future__ import annotations

from fastapi import APIRouter

from fastapi import HTTPException

from modules.akashic_sync_manager import manager

router = APIRouter()


@router.get("/robustness/akashic-sync")
def get_akashic_sync_state():
    return manager.get_state()


@router.post("/robustness/akashic-sync/thresholds")
def update_thresholds(payload: dict):
    try:
        latency = float(payload["latency_ms"])
        error_rate = float(payload["error_rate"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="latency_ms and error_rate are required numbers")
    manager.update_thresholds(latency, error_rate)
    return manager.get_state()["thresholds"]
