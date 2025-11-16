"Track security refresh history from logs/security_refresh.log."

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

LOG_PATH = Path("logs/security_refresh.log")


def read_recent_refresh_entries(limit: int = 5) -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        with LOG_PATH.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries[-limit:]


def has_recent_failures(entries: List[Dict[str, Any]], window: int = 3) -> bool:
    tail = entries[-window:] if window > 0 else entries
    return any(entry.get("errors") for entry in tail)


def recent_failure_details(entries: List[Dict[str, Any]], window: int = 3) -> Dict[str, Any]:
    tail = entries[-window:] if window > 0 else entries
    failures = [entry for entry in tail if entry.get("errors")]
    if not failures:
        return {"count": 0, "messages": []}
    messages = []
    for entry in failures:
        errors = entry.get("errors", [])
        if errors:
            messages.extend(errors)
    return {
        "count": len(failures),
        "messages": messages[:5],
    }
