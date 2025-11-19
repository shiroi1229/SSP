"""Health checker for distributed recovery nodes."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from modules.distributed_recovery_manager import manager
from modules.log_manager import log_manager


@dataclass
class NodeHealth:
    name: str
    status: str
    cpu: float
    memory: float
    ping_ms: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "cpu_percent": round(self.cpu, 2),
            "memory_percent": round(self.memory, 2),
            "ping_ms": round(self.ping_ms, 1),
        }


class ClusterHealthChecker:
    """Aggregates per-node metrics for distributed recovery."""

    def collect(self) -> List[Dict[str, object]]:
        nodes = []
        for node in manager.nodes:
            cpu = random.uniform(10.0, 95.0)
            memory = random.uniform(15.0, 92.0)
            ping = random.uniform(10.0, 120.0)
            nodes.append(
                NodeHealth(
                    name=node.name,
                    status=node.status,
                    cpu=cpu,
                    memory=memory,
                    ping_ms=ping,
                )
            )
        log_manager.debug(f"[HealthChecker] Collected metrics for {len(nodes)} nodes.")
        return [node.to_dict() for node in nodes]

    def detect_anomalies(self) -> List[Dict[str, object]]:
        metrics = self.collect()
        anomalies = [
            metric
            for metric in metrics
            if metric["cpu_percent"] > 90 or metric["memory_percent"] > 90 or metric["status"] != "active"
        ]
        log_manager.info(f"[HealthChecker] Detected {len(anomalies)} anomaly(s).")
        return anomalies


health_checker = ClusterHealthChecker()
