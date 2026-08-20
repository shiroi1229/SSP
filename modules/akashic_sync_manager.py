"""
Akashic Synchronization Nexus manager (R-v3.5).
Aggregates state from adaptive load balancer, distributed recovery, and loop health metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from modules.adaptive_load_balancer import balancer as load_balancer
from modules.distributed_recovery_manager import manager as recovery_manager

CONFIG_PATH = Path("config/akashic_sync_config.json")
LOOP_HEALTH_ENDPOINT = "logs/feedback_loop.log"


class AkashicSyncManager:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.sync_nodes = []
        self.thresholds = {}
        self.reload_config()

    def reload_config(self):
        if not self.config_path.exists():
            self.sync_nodes = recovery_manager.get_state()["nodes"]
            self.thresholds = {"latency_ms": 500, "error_rate": 0.05}
            return
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.sync_nodes = data.get("sync_nodes", [])
        self.thresholds = data.get("thresholds", {"latency_ms": 500, "error_rate": 0.05})

    def update_thresholds(self, latency_ms: float, error_rate: float):
        self.thresholds = {"latency_ms": latency_ms, "error_rate": error_rate}
        self.persist()

    def persist(self):
        data = {"sync_nodes": self.sync_nodes, "thresholds": self.thresholds}
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def loop_health_summary(self) -> Dict[str, Any]:
        # simple placeholder analysis of loop log (counts errors)
        log_path = Path(LOOP_HEALTH_ENDPOINT)
        errors = 0
        warnings = 0
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[-300:]:
                if "ERROR" in line:
                    errors += 1
                elif "WARN" in line or "WARNING" in line:
                    warnings += 1
        return {"errors": errors, "warnings": warnings}

    def get_state(self) -> Dict[str, Any]:
        load_state = load_balancer.get_state()
        recovery_state = recovery_manager.get_state()
        loop_state = self.loop_health_summary()
        alignment = "aligned"
        if (
            loop_state["errors"] > 0
            or loop_state["warnings"] > self.thresholds.get("error_rate", 0.05) * 100
            or load_state["metrics"]["cpu"] > self.thresholds.get("latency_ms", 500) / 1000.0
        ):
            alignment = "drift_detected"
        return {
            "syncNodes": self.sync_nodes,
            "thresholds": self.thresholds,
            "loadBalancer": load_state,
            "recovery": recovery_state,
            "loopHealth": loop_state,
            "alignment": alignment,
        }


manager = AkashicSyncManager()
