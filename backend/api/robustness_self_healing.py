from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()

SELF_HEALING_LOG = Path("logs/self_healing_daemon.log")


def _parse_line(line: str) -> Dict[str, Any]:
    ts = None
    level = "INFO"
    action = None
    if line[:19].replace('-', '').replace(':', '').replace(' ', '').isdigit():
        ts = line[:19]
        payload = line[20:]
    else:
        payload = line
    if "ERROR" in payload:
        level = "ERROR"
    elif "WARN" in payload or "WARNING" in payload:
        level = "WARN"
    if "action=" in payload:
        part = payload.split("action=", 1)[1]
        action = part.split()[0]
    return {
        "timestamp": ts,
        "level": level,
        "line": payload.strip(),
        "action": action,
    }


@router.get("/robustness/self-healing")
def get_self_healing_state(limit: int = 50):
    if not SELF_HEALING_LOG.exists():
        return {"events": [], "summary": {"errors": 0, "warnings": 0, "actions": {}}}

    lines = SELF_HEALING_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    parsed = [_parse_line(line) for line in lines[-500:]]
    events = parsed[-limit:]

    errors = sum(1 for e in parsed if e["level"] == "ERROR")
    warnings = sum(1 for e in parsed if e["level"] == "WARN")
    action_map: Dict[str, int] = {}
    for e in parsed:
        if e["action"]:
            action_map[e["action"]] = action_map.get(e["action"], 0) + 1

    return {
        "events": events,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "actions": action_map,
        },
    }
