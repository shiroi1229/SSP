"""Context rollback utilities for temporal recovery."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ContextRollback:
    def __init__(
        self,
        history_path: str = "logs/context_history.json",
        output_path: str = "data/context_rollback_snapshot.json",
        log_path: str = "logs/context_rollback.jsonl",
    ) -> None:
        self.history_path = Path(history_path)
        self.output_path = Path(output_path)
        self.log_path = Path(log_path)

    def rollback(self, timestamp: Optional[str], reason: str = "manual rollback") -> Dict[str, Any]:
        snapshots = self._load_history()
        if not snapshots:
            return {"success": False, "detail": "No context history available."}
        target = self._find_closest_snapshot(snapshots, timestamp)
        payload = {
            "restored_at": datetime.utcnow().isoformat(),
            "requested_timestamp": timestamp,
            "snapshot": target,
            "reason": reason,
        }
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["snapshot_file"] = str(self.output_path)
        log_entry = {
            "restored_at": payload["restored_at"],
            "requested_timestamp": timestamp,
            "reason": reason,
            "snapshot_file": payload["snapshot_file"],
        }
        self._append_log(log_entry)
        return {"success": True, "payload": payload, "log": log_entry}

    def _load_history(self):
        if not self.history_path.exists():
            return []
        return json.loads(self.history_path.read_text(encoding="utf-8"))

    def _find_closest_snapshot(self, snapshots, timestamp: Optional[str]):
        if not timestamp:
            return snapshots[-1]
        requested = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        best = snapshots[-1]
        best_diff = None
        for entry in snapshots:
            entry_ts = entry.get("timestamp") or entry.get("created_at")
            if not entry_ts:
                continue
            current = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
            diff = abs((current - requested).total_seconds())
            if best_diff is None or diff < best_diff:
                best = entry
                best_diff = diff
        return best

    def _append_log(self, entry: Dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


rollback_manager = ContextRollback()
