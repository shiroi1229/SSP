"""
Luminous Nexus manager (R-v4.5).
Manages multi-region recovery clusters and automatic cross-sync actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

CONFIG_PATH = Path("config/luminous_nexus_config.json")


@dataclass
class ClusterNode:
    name: str
    status: str


@dataclass
class Cluster:
    name: str
    nodes: List[ClusterNode] = field(default_factory=list)


class LuminousNexusManager:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.clusters: List[Cluster] = []
        self.reload_config()

    def reload_config(self):
        if not self.config_path.exists():
            self.clusters = []
            return
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.clusters = [
            Cluster(name=cluster["name"], nodes=[ClusterNode(**node) for node in cluster.get("nodes", [])])
            for cluster in data.get("clusters", [])
        ]

    def persist(self):
        data = {
            "clusters": [
                {"name": cluster.name, "nodes": [node.__dict__ for node in cluster.nodes]}
                for cluster in self.clusters
            ]
        }
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_state(self) -> Dict[str, Any]:
        return {"clusters": [ {"name": c.name, "nodes": [node.__dict__ for node in c.nodes]} for c in self.clusters ]}

    def sync_cluster(self, cluster_name: str, target_status: str):
        cluster = next((c for c in self.clusters if c.name == cluster_name), None)
        if not cluster:
            raise ValueError("Cluster not found")
        for node in cluster.nodes:
            node.status = target_status
        self.persist()
        return cluster_name


manager = LuminousNexusManager()
