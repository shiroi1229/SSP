# path: modules/distributed_persona_fabric.py
# version: v1
# 目的: 複数のAI人格を生成し、思考・評価・協調・競合を通じて最適解を導く。

import json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from modules.self_reasoning_loop import SelfReasoningLoop

LOG_PATH = "logs/persona_fabric_log.json"

class Persona:
    """独立したAI人格ユニット"""
    def __init__(self, name: str, bias: float):
        self.name = name
        self.bias = bias
        self.loop = SelfReasoningLoop()

    def think(self):
        record = self.loop.loop_once()
        record["persona"] = self.name
        record["bias"] = self.bias
        record["adjusted_score"] = round(record["score"] * self.bias, 2)
        return record


class DistributedPersonaFabric:
    """複数人格の並行思考と統合"""
    def __init__(self, persona_count: int = 3):
        self.personas = [
            Persona(f"Shiroi_{i+1}", random.uniform(0.8, 1.2))
            for i in range(persona_count)
        ]
        self.history = []

    def simulate_collective_thinking(self, cycles: int = 2):
        """複数人格が並行して思考し、その結果を統合"""
        results = []
        with ThreadPoolExecutor(max_workers=len(self.personas)) as executor:
            futures = [executor.submit(p.think) for p in self.personas]
            for f in as_completed(futures):
                results.append(f.result())

        avg_score = round(sum(r["adjusted_score"] for r in results) / len(results), 2)
        consensus = {
            "timestamp": datetime.now().isoformat(),
            "personas": [r["persona"] for r in results],
            "avg_score": avg_score,
            "individual_thoughts": [r["thought"] for r in results],
            "collective_decision": self.resolve_conflict(results)
        }

        self.history.append(consensus)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(consensus, ensure_ascii=False) + "\n")

        return consensus

    def resolve_conflict(self, results):
        """人格間の思考差異を解析し、統合判断を返す"""
        ideas = [r["thought"] for r in results]
        unique_ideas = list(set(ideas))
        if len(unique_ideas) == 1:
            return unique_ideas[0]
        else:
            # もっともスコアの高い人格の意見を代表に採用
            top = max(results, key=lambda x: x["adjusted_score"])
            return f"Consensus led by {top['persona']}: {top['thought']}"
