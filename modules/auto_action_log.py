"""Store and retrieve auto action logs for Insight and meta-causal systems."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

LOG_PATH = Path("logs/auto_actions.jsonl")


def log_action(action: Dict[str, object], success: bool | None = None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if success is None and isinstance(action.get("success"), bool):
        success = action.get("success")
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "action_type": action.get("type", "unknown"),
        "success": bool(success) if success is not None else True,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_actions(limit: int = 50) -> List[Dict[str, object]]:
    if not LOG_PATH.exists():
        return []
    entries = []
    with LOG_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries[-limit:]
