"""Timeline rebuilder for R-v0.7."""

from __future__ import annotations

import json
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

    def rebuild_timeline(self, limit: int = 50, layer: str | None = None) -> Dict[str, Any]:
        history = self._load_history()
        if not history:
            return {
                "timeline": [],
                "summary": {
                    "entries": 0,
                    "gaps_detected": 0,
                    "needs_rollback": False,
                    "recommended_timestamp": None,
                    "snapshots_available": 0,
                    "layer": layer,
                },
            }

        filtered = [
            entry
            for entry in history
            if layer is None or entry.get("layer") == layer or entry.get("key") == layer
        ]
        if not filtered:
            return {
                "timeline": [],
                "summary": {
                    "entries": 0,
                    "gaps_detected": 0,
                    "needs_rollback": False,
                    "recommended_timestamp": None,
                    "snapshots_available": 0,
                    "layer": layer,
                },
                "notice": f"No timeline entries found for layer '{layer}'.",
            }

        selected = filtered[-limit:]
        timeline: List[Dict[str, Any]] = []
        gaps = 0
        recommendation_ts: str | None = None
        snapshots_available = 0

        for entry in selected:
            ts = entry.get("timestamp") or entry.get("created_at")
            entry_layer = entry.get("layer", "unknown")
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

            if status == "missing" and recommendation_ts is None and ts:
                recommendation_ts = ts

            snapshot_path = self._snapshot_path(ts)
            if snapshot_path:
                snapshots_available += 1

            timeline.append(
                {
                    "timestamp": ts,
                    "layer": entry_layer,
                    "note": note,
                    "status": status,
                    "has_snapshot": bool(snapshot_path),
                    "snapshot_path": snapshot_path,
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
                "needs_rollback": recommendation_ts is not None,
                "recommended_timestamp": recommendation_ts,
                "snapshots_available": snapshots_available,
                "layer": layer,
            },
        }

    def _snapshot_path(self, timestamp: str | None) -> str | None:
        if not timestamp:
            return None
        sanitized = timestamp.replace(":", "-")
        for candidate in self.snapshot_dir.glob(f"*{sanitized}*.json"):
            if candidate.exists():
                return str(candidate)
        return None

    def _snapshot_exists(self, timestamp: str | None) -> bool:
        return self._snapshot_path(timestamp) is not None


rebuilder = TimelineRebuilder()
