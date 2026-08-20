"""
Existential Resilience manager (R-v4.0).
Applies Akashic thresholds to trigger auto actions (hot patch, restart).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from modules.akashic_sync_manager import manager as akashic_manager

CONFIG_PATH = Path("config/existential_resilience_config.json")


class ExistentialResilienceManager:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.auto_actions: List[Dict[str, Any]] = []
        self.reload_config()

    def reload_config(self):
        if not self.config_path.exists():
            self.auto_actions = [
                {"name": "hot_patch", "enabled": True, "trigger": "alignment_drift"},
                {"name": "restart_loop", "enabled": False, "trigger": "error_spike"},
            ]
            return
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.auto_actions = data.get("auto_actions", [])

    def persist(self):
        data = {"auto_actions": self.auto_actions}
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_state(self) -> Dict[str, Any]:
        akashic_state = akashic_manager.get_state()
        actions_taken = []
        if akashic_state["alignment"] == "drift_detected":
            actions_taken.append("trigger_hot_patch")
        if akashic_state["loopHealth"]["errors"] > 5:
            actions_taken.append("restart_loop")
        return {"autoActions": self.auto_actions, "akashicState": akashic_state, "actionsTaken": actions_taken}

    def update_actions(self, actions: List[Dict[str, Any]]):
        self.auto_actions = actions
        self.persist()


manager = ExistentialResilienceManager()
