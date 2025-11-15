"""
Distributed Recovery System for R-v0.5.

Keeps track of recovery nodes and can promote standby nodes when primary is unhealthy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

CONFIG_PATH = Path("config/distributed_recovery_config.json")


@dataclass
class RecoveryNode:
    name: str
    role: str
    status: str


class DistributedRecoveryManager:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.nodes: List[RecoveryNode] = []
        self.reload_config()

    def reload_config(self):
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.nodes = [RecoveryNode(**node) for node in data.get("nodes", [])]

    def get_state(self) -> dict:
        return {"nodes": [node.__dict__ for node in self.nodes]}

    def promote(self, standby_name: str) -> dict:
        primary = next((n for n in self.nodes if n.role == "primary"), None)
        standby = next((n for n in self.nodes if n.name == standby_name), None)
        if not standby:
            raise ValueError("Standby node not found")
        if primary:
            primary.role = "standby"
            primary.status = "demoted"
        standby.role = "primary"
        standby.status = "active"
        self._persist()
        return {"primary": standby.name}

    def toggle_status(self, name: str, status: str) -> dict:
        node = next((n for n in self.nodes if n.name == name), None)
        if not node:
            raise ValueError("Node not found")
        node.status = status
        self._persist()
        return node.__dict__

    def _persist(self):
        data = {"nodes": [node.__dict__ for node in self.nodes]}
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


manager = DistributedRecoveryManager()
