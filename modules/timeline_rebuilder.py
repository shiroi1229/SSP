"""Timeline rebuilder for R-v0.7."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class TimelineRebuilder:
    def __init__(
        self,
        history_path: str = "logs/context_history.json",
        snapshot_dir: str = "logs/context_evolution",
    ) -> None:
        self.history_path = Path(history_path)
        self.snapshot_dir = Path(snapshot_dir)

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_path.exists():
            return []
        data = json.loads(self.history_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []

    def rebuild_timeline(self, limit: int = 50) -> Dict[str, Any]:
        history = self._load_history()
        if not history:
            return {"timeline": [], "summary": {"entries": 0, "gaps_detected": 0}}

        selected = history[-limit:]
        timeline: List[Dict[str, Any]] = []
        gaps = 0
        for entry in selected:
            ts = entry.get("timestamp") or entry.get("created_at")
            layer = entry.get("layer", "unknown")
            note = entry.get("reason") or entry.get("key")
            new_value = entry.get("new_value")
            old_value = entry.get("old_value")
            status = "stable"
            if new_value is None and old_value is None:
                status = "missing"
                gaps += 1
            elif new_value and not old_value:
                status = "restored"
            elif old_value and not new_value:
                status = "dropped"
            else:
                status = "updated"
            timeline.append(
                {
                    "timestamp": ts,
                    "layer": layer,
                    "note": note,
                    "status": status,
                    "has_snapshot": self._snapshot_exists(ts),
                }
            )

        return {
            "timeline": sorted(
                timeline,
                key=lambda item: item.get("timestamp") or "",
                reverse=True,
            ),
            "summary": {
                "entries": len(timeline),
                "gaps_detected": gaps,
            },
        }

    def _snapshot_exists(self, timestamp: str | None) -> bool:
        if not timestamp:
            return False
        sanitized = timestamp.replace(":", "-")
        for candidate in self.snapshot_dir.glob(f"*{sanitized}*.json"):
            if candidate.exists():
                return True
        return False


rebuilder = TimelineRebuilder()
