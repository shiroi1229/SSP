from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modules.luminous_nexus_manager import manager

router = APIRouter()


@router.get("/robustness/luminous-nexus")
def get_luminous_state():
    return manager.get_state()


@router.post("/robustness/luminous-nexus/sync")
def sync_cluster(payload: dict):
    cluster = payload.get("cluster")
    status = payload.get("status", "syncing")
    if not cluster:
        raise HTTPException(status_code=400, detail="cluster is required")
    try:
        manager.sync_cluster(cluster, status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return manager.get_state()
