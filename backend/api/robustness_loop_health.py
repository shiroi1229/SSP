from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter

router = APIRouter()

FEEDBACK_LOG = Path("logs/feedback_loop.log")


def _parse_feedback_lines(limit: int = 200) -> List[Dict[str, str]]:
    if not FEEDBACK_LOG.exists():
        return []
    lines = FEEDBACK_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    events: List[Dict[str, str]] = []
    for line in lines[-limit:]:
        if " - " in line:
            try:
                timestamp, rest = line.split(" - ", 1)
                level, message = rest.split(" - ", 1)
            except ValueError:
                events.append({"timestamp": "", "level": "INFO", "message": line})
            else:
                events.append({"timestamp": timestamp.strip(), "level": level.strip(), "message": message.strip()})
        else:
            events.append({"timestamp": "", "level": "INFO", "message": line})
    return events[-100:]


@router.get("/robustness/loop-health")
def get_loop_health_state():
    events = _parse_feedback_lines()
    error_count = sum(1 for e in events if "ERROR" in e["level"])
    warning_count = sum(1 for e in events if "WARN" in e["level"] or "WARNING" in e["level"])
    recovery_actions = sum(1 for e in events if "[Recovery]" in e["message"] or "rollback" in e["message"].lower())
    last_error = next((e for e in reversed(events) if "ERROR" in e["level"]), None)

    summary = {
        "errorCount": error_count,
        "warningCount": warning_count,
        "recoveryActions": recovery_actions,
        "lastError": last_error,
    }

    return {
        "summary": summary,
        "events": events,
    }
