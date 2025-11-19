"""Awareness observer utilities for the Cognitive Mirror."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from modules.awareness_observer import build_snapshot_payload

LOGS_DIR = Path("logs")
DEFAULT_LOG_PATHS: Dict[str, Path] = {
    "feedback_loop": LOGS_DIR / "feedback_loop.log",
    "introspection": LOGS_DIR / "introspection_trace.log",
    "context_history": LOGS_DIR / "context_history.json",
}


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except Exception:
        return 0


class AwarenessObserver:
    """Collects awareness metrics by reading logs and assembling snapshots."""

    def __init__(self, log_paths: Dict[str, Path] | None = None) -> None:
        self.log_paths = log_paths or DEFAULT_LOG_PATHS

    def collect(self) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        snapshot = build_snapshot_payload()
        log_counts = {name: _count_lines(path) for name, path in self.log_paths.items()}
        return {
            "timestamp": timestamp,
            "snapshot": snapshot,
            "log_counts": log_counts,
            "observation_summary": {
                "files": list(self.log_paths.keys()),
                "snapshot_available": bool(snapshot),
            },
        }
