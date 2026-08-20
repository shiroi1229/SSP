# path: modules/cognitive_graph_engine.py
# version: v1
# 目的: モジュール・契約・文脈・感情・記憶の関係を意味グラフとして表現・探索する

import networkx as nx
import json
from pathlib import Path

GRAPH_PATH = Path("data/cognitive_graph.json")

class CognitiveGraphEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        if GRAPH_PATH.exists():
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.graph.add_nodes_from(data.get("nodes", []))
                self.graph.add_edges_from(data.get("edges", []))

    def add_relation(self, source: str, relation: str, target: str):
        """ノード間に意味関係を追加"""
        self.graph.add_node(source)
        self.graph.add_node(target)
        self.graph.add_edge(source, target, relation=relation)

    def find_path(self, start: str, end: str):
        """意味関係経路を探索"""
        try:
            path = nx.shortest_path(self.graph, start, end)
            return {"path": path}
        except nx.NetworkXNoPath:
            return {"error": "No path found."}

    def export(self):
        """グラフをJSONとして保存"""
        data = {
            "nodes": list(self.graph.nodes),
            "edges": [(u, v, self.graph[u][v]) for u, v in self.graph.edges],
        }
        GRAPH_PATH.parent.mkdir(exist_ok=True)
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(GRAPH_PATH)
