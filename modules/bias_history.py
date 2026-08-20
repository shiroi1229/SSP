from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

HISTORY_PATH = Path("logs/bias_history.jsonl")


def add_bias_record(bias_report: Dict[str, object]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "report": bias_report,
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_bias_history(limit: int = 100) -> List[Dict[str, object]]:
    if not HISTORY_PATH.exists():
        return []
    entries: List[Dict[str, object]] = []
    with HISTORY_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries[-limit:]


def compute_long_term_bias(limit: int = 200) -> Dict[str, object]:
    history = load_bias_history(limit)
    emotion_totals: Dict[str, float] = {}
    knowledge_totals: Dict[str, float] = {}
    timeline: List[Dict[str, object]] = []
    for entry in history:
        report = entry.get("report", {})
        emotion_items = _coerce_biases(report.get("emotion_bias", []))
        knowledge_items = _coerce_biases(report.get("knowledge_bias", []))

        for item in emotion_items:
            emotion_totals[item["label"]] = emotion_totals.get(item["label"], 0.0) + float(item["score"])
        for item in knowledge_items:
            knowledge_totals[item["label"]] = knowledge_totals.get(item["label"], 0.0) + float(item["score"])

        timeline.append(
            {
                "timestamp": entry.get("timestamp"),
                "emotion": _top_biases(emotion_items),
                "knowledge": _top_biases(knowledge_items),
            }
        )
    normalized_emotion = _normalize(emotion_totals)
    normalized_knowledge = _normalize(knowledge_totals)
    return {
        "history_length": len(history),
        "emotion_average": normalized_emotion,
        "knowledge_average": normalized_knowledge,
        "timeline": timeline,
        "alerts": _derive_alerts(timeline),
    }


def _normalize(totals: Dict[str, float]) -> List[Dict[str, float]]:
    total = sum(totals.values()) or 1.0
    data = [
        {"label": k, "score": round(v / total, 3)}
        for k, v in totals.items()
    ]
    return sorted(data, key=lambda item: item["score"], reverse=True)[:5]


def _coerce_biases(items: List[Dict[str, float]]) -> List[Dict[str, float]]:
    normalized: List[Dict[str, float]] = []
    for item in items or []:
        label = item.get("label")
        score = item.get("score")
        if label is None or score is None:
            continue
        normalized.append({"label": str(label), "score": float(score)})
    return normalized


def _top_biases(items: List[Dict[str, float]], top_n: int = 3) -> List[Dict[str, float]]:
    if not items:
        return []
    return sorted(items, key=lambda item: item["score"], reverse=True)[:top_n]


def _derive_alerts(timeline: List[Dict[str, object]]) -> List[Dict[str, object]]:
    alerts: List[Dict[str, object]] = []
    prev_emotion = None
    prev_knowledge = None

    for point in timeline:
        timestamp = point.get("timestamp")
        top_emotion = point["emotion"][0] if point["emotion"] else None
        top_knowledge = point["knowledge"][0] if point["knowledge"] else None

        prev_emotion = _maybe_add_alert(
            alerts, timestamp, "emotion", top_emotion, prev_emotion
        )
        prev_knowledge = _maybe_add_alert(
            alerts, timestamp, "knowledge", top_knowledge, prev_knowledge
        )

    return alerts[-8:]


def _maybe_add_alert(
    alerts: List[Dict[str, object]],
    timestamp: str | None,
    bias_type: str,
    current: Dict[str, float] | None,
    previous: Dict[str, float] | None,
) -> Dict[str, float] | None:
    if not current:
        return previous

    score = float(current["score"])
    severity = None
    message = None

    if score >= 0.45:
        severity = "high"
        message = f"{current['label']} の偏向が {score:.2f}"
    elif previous:
        delta = score - float(previous.get("score", 0.0))
        if abs(delta) >= 0.18:
            severity = "shift"
            direction = "上昇" if delta > 0 else "減衰"
            message = f"{current['label']} が{direction} ({delta:+.2f})"

    if severity and message:
        alerts.append(
            {
                "timestamp": timestamp,
                "type": bias_type,
                "label": current["label"],
                "score": round(score, 3),
                "severity": severity,
                "message": message,
            }
        )

    return {"label": current["label"], "score": score}
