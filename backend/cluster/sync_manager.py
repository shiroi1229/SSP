"""Sync manager for propagating session + cache state across clusters."""

from __future__ import annotations

from modules.state_resync import capture_state_snapshot
from modules.log_manager import log_manager


class SyncManager:
    def __init__(self):
        self.history = []

    def sync(self, node_name: str) -> Dict[str, object]:
        snapshot = capture_state_snapshot()
        payload = {"node": node_name, "snapshot": snapshot.get("path")}
        self.history.append(payload)
        log_manager.info(f"[SyncManager] Node {node_name} synced with snapshot {snapshot.get('path')}")
        if len(self.history) > 10:
            self.history.pop(0)
        return payload


sync_manager = SyncManager()
