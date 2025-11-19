# path: modules/metacognition.py
# version: v1.9
"""
Cognitive Harmony Extension
----------------------------------------
Evaluates alignment between emotional valence and logical confidence.
Enables Shiroi to measure her internal cognitive balance.
"""

import os, json, datetime, logging
import re
import numpy as np
import statistics

LOG_PATH = "./logs/introspection_trace.log"
PERSONA_PROFILE_PATH = "./config/persona_profile.json" # Moved up for visibility
MAX_ENTRIES = 5000

# 感情語辞書（暫定）
EMOTION_MAP = {
    "嬉": (0.8, 0.6), "楽": (0.9, 0.8), "悲": (-0.8, 0.5),
    "怒": (-0.7, 0.9), "恐": (-0.9, 0.8), "安": (0.7, 0.3),
    "驚": (0.3, 0.9), "退": (-0.6, 0.4), "好": (0.9, 0.5)
}

def analyze_emotion(text: str):
    """Return (valence, arousal) from text content."""
    valence, arousal, count = 0.0, 0.0, 0
    for key, (v, a) in EMOTION_MAP.items():
        if key in text:
            valence += v
            arousal += a
            count += 1
    if count == 0:
        return (0.0, 0.0)
    return (round(valence/count, 2), round(arousal/count, 2))

def log_introspection(stage: str, thought: str, confidence: float = 0.7):
    """Record a thought into the introspection log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    valence, arousal = analyze_emotion(thought)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "stage": stage,
        "thought": thought.strip(),
        "confidence": round(confidence, 2),
        "emotion": {"valence": valence, "arousal": arousal}
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    _truncate_if_needed()
    logging.info(f"[Metacognition] {stage}: {thought}")
    return entry

def summarize_introspection(limit: int = 10):
    """
    Summarize recent introspections for reflection."""
    if not os.path.exists(LOG_PATH):
        return "No introspection logs yet."

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]

    data = []
    for line in lines:
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError as e:
            logging.warning(f"Could not decode JSON from introspection log line: {line.strip()}. Error: {e}")
            continue

    thoughts = [f"{d['stage']}: {d['thought']}" for d in data]
    avg_conf = round(sum(d['confidence'] for d in data) / len(data), 2) if data else 0.0
    summary = " / ".join(thoughts)

    return {
        "entries": len(data),
        "average_confidence": avg_conf,
        "summary": summary
    }

def _truncate_if_needed():
    """Auto-truncate old logs when exceeding MAX_ENTRIES."""
    if not os.path.exists(LOG_PATH):
        return
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) > MAX_ENTRIES:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines[-MAX_ENTRIES:])

def compute_cognitive_harmony(valence: float, confidence: float) -> float:
    """
    Harmony Score ∈ [-1.0, +1.0]
      +1.0 → 感情と論理が完全一致（安定）
       0.0 → 無関係（中立）
      -1.0 → 感情と論理が逆方向（葛藤）
    """
    if valence == 0 and confidence == 0:
        return 0.0

    # Normalize both to -1〜+1 range
    val = max(-1.0, min(1.0, valence))
    conf = max(0.0, min(1.0, confidence))
    harmony = (val * 2 - 1) * (conf * 2 - 1)  # signed alignment
    return round(harmony, 2)

def extract_emotional_patterns():
    file = "./logs/introspection_trace.log"
    if not os.path.exists(file):
        return {"average_valence": 0, "dominant_emotion": "neutral"}

    with open(file, "r", encoding="utf-8") as f:
        data = [json.loads(x) for x in f.readlines() if "emotion" in x]
    valences = [d["emotion"]["valence"] for d in data if "emotion" in d]
    if not valences:
        return {"average_valence": 0, "dominant_emotion": "neutral"}

    avg_val = round(statistics.mean(valences), 2)
    dominant = "positive" if avg_val > 0 else "negative" if avg_val < 0 else "neutral"
    return {"average_valence": avg_val, "dominant_emotion": dominant}

def get_latest_introspection_log():
    """Retrieve the most recent introspection log entry."""
    if not os.path.exists(LOG_PATH):
        return {"summary": "No introspection logs yet."}

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return {"summary": "No introspection logs yet."}
        
        last_line = lines[-1]
        try:
            return json.loads(last_line)
        except json.JSONDecodeError as e:
            logging.warning(f"Could not decode JSON from last introspection log line: {last_line.strip()}. Error: {e}")
            return {"summary": "Error reading last log entry."}

def get_cognitive_graph_data():
    """Retrieve cognitive traits from persona_profile.json."""
    if not os.path.exists(PERSONA_PROFILE_PATH):
        logging.warning(f"Persona profile not found at {PERSONA_PROFILE_PATH}. Returning default traits.")
        return {
            "assertiveness": 0.5,
            "empathy": 0.5,
            "curiosity": 0.5,
            "stability": 0.5,
            "creativity": 0.5,
        }
    try:
        with open(PERSONA_PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("traits", {})
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding persona profile JSON: {e}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(f"Error reading persona profile: {e}", exc_info=True)
        return {}
