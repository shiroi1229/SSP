from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

RULES_FILE = Path("config/loop_health_rules.json")


def load_rules() -> List[Dict[str, Any]]:
    if not RULES_FILE.exists():
        return []
    try:
        data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Failed to parse loop health rules.") from exc
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="Loop health rules must be a list.")
    return data


@router.get("/robustness/loop-health/rules")
def get_loop_health_rules():
    return {"rules": load_rules()}
