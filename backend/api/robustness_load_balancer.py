from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException

from modules.adaptive_load_balancer import balancer, CONFIG_PATH

router = APIRouter()


@router.get("/robustness/load-balancer")
def get_load_balancer_state():
    return balancer.get_state()


@router.post("/robustness/load-balancer/rules")
def update_load_balancer_rules(payload: dict):
    if "modes" not in payload or not isinstance(payload["modes"], list):
        raise HTTPException(status_code=400, detail="modes list is required")

    CONFIG_PATH.write_text(json.dumps({"modes": payload["modes"]}, indent=2), encoding="utf-8")
    balancer.reload_config()
    return {"status": "updated", "modes": balancer.get_state()["modes"]}
