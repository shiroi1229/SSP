# path: modules/evolution_mirror.py
# version: v1
# 目的: SSPの進化過程を観測・評価・記録し、メタ学習フィードバックを生成する

import json
from datetime import datetime
from pathlib import Path
import statistics

LOG_PATH = Path("logs/evolution_mirror_log.json")

class EvolutionMirror:
    """システム全体の進化を観測・記録・解析する自己反省エンジン"""

    def __init__(self):
        self.records = []

    def observe(self, event_type: str, data: dict):
        """任意のシステムイベントを観測ログとして記録"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "metrics": data,
        }
        self.records.append(record)
        LOG_PATH.parent.mkdir(exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def evaluate_progress(self):
        """ログから進化の傾向を定量的に評価"""
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f.readlines()]

            scores = [e["metrics"].get("score", 0) for e in logs if "metrics" in e]
            if not scores:
                return {"summary": "No progress data yet."}

            avg = round(statistics.mean(scores), 2)
            stdev = round(statistics.pstdev(scores), 2)
            trend = "upward" if avg > 3 else "neutral" if avg == 3 else "declining"

            return {
                "avg_score": avg,
                "stability": stdev,
                "trend": trend,
                "log_count": len(scores),
            }
        except Exception as e:
            return {"error": str(e)}

    def reflect(self):
        """自己分析結果を返す（自己診断）"""
        eval_data = self.evaluate_progress()
        summary = {
            "timestamp": datetime.now().isoformat(),
            "self_diagnosis": eval_data,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary
