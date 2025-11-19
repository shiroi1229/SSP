"""Recovery agent orchestrates failover for R-v0.5 clusters."""

from __future__ import annotations

from typing import Dict

from modules.distributed_recovery_manager import manager as recovery_manager
from modules.failure_logger import failure_logger
from modules.state_resync import capture_state_snapshot
from modules.log_manager import log_manager


class RecoveryAgent:
    def promote(self, node_name: str) -> Dict[str, object]:
        result = recovery_manager.promote(node_name)
        failure_logger.log_info("Cluster recovery promoted node", {"node": node_name})
        return {"promoted": result}

    def heal(self, node_name: str) -> Dict[str, object]:
        snapshot = capture_state_snapshot()
        failure_logger.log_info("Cluster recovery syncing state", {"node": node_name})
        return {"node": node_name, "snapshot": snapshot.get("path")}


recovery_agent = RecoveryAgent()
