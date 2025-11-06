# path: modules/collective_intelligence_core.py
# version: v1
# 目的: 複数Personaの思考結果を統合・評価し、集団知的意思を生成する。

import json
import statistics
from datetime import datetime
from pathlib import Path
from modules.distributed_persona_fabric import DistributedPersonaFabric

LOG_PATH = Path("logs/collective_core_log.json")

class CollectiveIntelligenceCore:
    """群知能の中枢層：複数Personaの出力を統合・最適化"""

    def __init__(self, personas: int = 3, cycles: int = 2):
        self.fabric = DistributedPersonaFabric(persona_count=personas)
        self.cycles = cycles

    def aggregate_decisions(self):
        """複数のPersonaから得られた意思決定を統合"""
        all_scores = []
        all_decisions = []

        for i in range(self.cycles):
            consensus = self.fabric.simulate_collective_thinking()
            all_scores.append(consensus["avg_score"])
            all_decisions.append(consensus["collective_decision"])

        # 平均・分散・トレンドを計算
        avg = round(statistics.mean(all_scores), 2)
        stdev = round(statistics.pstdev(all_scores), 2)
        final = self._vote(all_decisions)

        record = {
            "timestamp": datetime.now().isoformat(),
            "avg_collective_score": avg,
            "score_stability": stdev,
            "final_decision": final,
            "persona_count": len(self.fabric.personas),
            "cycles": self.cycles
        }

        LOG_PATH.parent.mkdir(exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def _vote(self, decisions):
        """決定内容の多数決 + 感情的重みの疑似考慮"""
        tally = {}
        for d in decisions:
            tally[d] = tally.get(d, 0) + 1
        top = max(tally, key=tally.get)
        return f"🧭 Collective Consensus: {top}"
