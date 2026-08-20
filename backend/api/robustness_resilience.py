from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modules.existential_resilience_manager import manager

router = APIRouter()


@router.get("/robustness/existential-resilience")
def get_resilience_state():
    return manager.get_state()


@router.post("/robustness/existential-resilience/actions")
def update_resilience_actions(payload: dict):
    actions = payload.get("autoActions")
    if not isinstance(actions, list):
        raise HTTPException(status_code=400, detail="autoActions list required")
    manager.update_actions(actions)
    return manager.get_state()
