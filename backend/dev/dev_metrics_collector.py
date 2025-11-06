# path: backend/dev/dev_metrics_collector.py
# version: v1
"""
開発効率メトリクス収集モジュール
Geminiが自分の開発行動を評価するための基盤
"""
import os, json, time
from datetime import datetime

LOG_DIR = "./logs/devstats"
os.makedirs(LOG_DIR, exist_ok=True)

def record_metric(action: str, detail: str, score: float = 1.0):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "detail": detail,
        "score": score,
    }
    path = os.path.join(LOG_DIR, "metrics.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

def summarize():
    path = os.path.join(LOG_DIR, "metrics.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f.readlines()]
    total = len(lines)
    avg_score = sum([l["score"] for l in lines]) / max(1, total)
    summary = {
        "total_actions": total,
        "average_score": round(avg_score, 2),
        "last_action": lines[-1] if total else None,
    }
    with open(os.path.join(LOG_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary
