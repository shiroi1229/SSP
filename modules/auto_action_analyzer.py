from __future__ import annotations

from typing import Dict

from modules.auto_action_log import read_actions


def compute_action_stats(limit: int = 200) -> Dict[str, Dict[str, float]]:
    entries = read_actions(limit)
    stats: Dict[str, Dict[str, float]] = {}
    for entry in entries:
        action_type = entry.get("action_type") or entry.get("action", {}).get("type", "unknown")
        record = stats.setdefault(action_type, {"count": 0, "success": 0})
        record["count"] += 1
        if entry.get("success"):
            record["success"] += 1
    for record in stats.values():
        count = record["count"] or 1
        record["success_ratio"] = round(record["success"] / count, 3)
    return stats


def should_execute(action_type: str, stats: Dict[str, Dict[str, float]], min_ratio: float = 0.4) -> bool:
    record = stats.get(action_type)
    if not record or record["count"] < 5:
        return True
    return record.get("success_ratio", 0.0) >= min_ratio
