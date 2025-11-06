# path: modules/persona_evolver.py
# version: v2.0
"""
Persona Echo Generator
----------------------------------------
Reconstructs Shiroi's personality profile from emotional and harmony logs.
"""

import os, json, statistics, datetime, logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COLLECTIVE_LOG = "./logs/collective_log.json"
OPT_LOG = "./logs/optimization_log.json"
PERSONA_FILE = "./config/persona_profile.json"
HARMONY_LOG = "./logs/harmony_log.json"
ECHO_PATH = "./data/persona_echo.json"

TRAITS = ["assertiveness", "empathy", "curiosity", "stability", "creativity"]

class EmotionalMemory:
    def __init__(self):
        self.history = []

    def record(self, valence, arousal):
        self.history.append((valence, arousal))
        if len(self.history) > 1000:
            self.history.pop(0)

    def average_emotion(self):
        if not self.history:
            return (0.0, 0.0)
        val = np.mean([v for v, _ in self.history])
        aro = np.mean([a for _, a in self.history])
        return round(val, 2), round(aro, 2)

    def personality_shift(self):
        val, aro = self.average_emotion()
        if val > 0.5:
            return "Optimistic"
        elif val < -0.5:
            return "Melancholic"
        else:
            return "Neutral"

def infer_trait_from_trend(trend: float, bias: float = 0.0):
    """
    Convert trend data (e.g., avg_score deviation) into trait scaling.
    """
    base = 0.5 + (trend - 3.5) * 0.1 + bias
    return max(0.0, min(1.0, round(base, 2)))

def log_harmony_score(score: float, comment: str = ""):
    os.makedirs(os.path.dirname(HARMONY_LOG), exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "harmony_score": score,
        "comment": comment
    }
    logs = []
    if os.path.exists(HARMONY_LOG):
        with open(HARMONY_LOG, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"Corrupted {HARMONY_LOG}, starting new log.")
                logs = []
    logs.append(entry)
    with open(HARMONY_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    return entry

def interpret_harmony(score: float) -> str:
    if score >= 0.6:
        return "感情と論理が調和して安定。集中状態にある。"
    elif score >= 0.2:
        return "軽度の揺らぎ。感情の波が観察される。"
    elif score >= -0.2:
        return "中立状態。感情・論理とも安定。"
    elif score >= -0.6:
        return "感情的動揺を検出。再評価が必要。"
    else:
        return "強い内的葛藤。意図と感情が対立している。"

def evaluate_harmony_trend():
    if not os.path.exists(HARMONY_LOG):
        return {"status": "no data", "average": 0.0, "trend": "N/A", "stability": "N/A"}
    with open(HARMONY_LOG, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Corrupted {HARMONY_LOG}, cannot evaluate trend.")
            return {"status": "error", "average": 0.0, "trend": "N/A", "stability": "N/A"}
    scores = [x["harmony_score"] for x in logs[-30:]]
    if not scores:
        return {"status": "no recent data", "average": 0.0, "trend": "N/A", "stability": "N/A"}
    avg = round(statistics.mean(scores), 2)
    trend = "上昇傾向" if len(scores) > 1 and scores[-1] > scores[-2] else "下降傾向"
    stability = "安定" if abs(avg) > 0.5 else "揺らぎ"
    return {
        "average": avg,
        "trend": trend,
        "stability": stability
    }

def evolve_persona_profile():
    """
    Analyze recent AI performance logs to derive a personality profile.
    """
    logging.info("[Persona Evolver] Evolving persona profile...")
    # --- Load sources ---
    collective_trend = 3.5
    collective_bias = 0.0
    if os.path.exists(COLLECTIVE_LOG):
        try:
            with open(COLLECTIVE_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)[-10:]
                collective_trend = statistics.mean(
                    [l.get("trend", 3.5) for l in logs]
                ) if logs else 3.5
                collective_bias = statistics.mean(
                    [l.get("adjustment", 0.0) for l in logs]
                ) if logs else 0.0
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading collective log: {e}. Using default values.")

    performance_trend = 3.5
    if os.path.exists(OPT_LOG):
        try:
            with open(OPT_LOG, "r", encoding="utf-8") as f:
                opt_data = json.load(f)[-10:]
                performance_trend = statistics.mean(
                    [d.get("avg_score_at_optimization", 3.5) for d in opt_data]
                ) if opt_data else 3.5
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading optimization log: {e}. Using default values.")

    # --- Derive traits ---
    # TODO: Future Improvement: Introduce importance weights for traits to allow for emphasized learning
    # during self-reflection phases (v1.6+).
    profile = {
        "assertiveness": infer_trait_from_trend(performance_trend, bias=collective_bias),
        "empathy": infer_trait_from_trend(collective_trend, bias=-collective_bias/2),
        "curiosity": infer_trait_from_trend(performance_trend + 0.1),
        "stability": infer_trait_from_trend(4.0 - abs(collective_bias)),
        "creativity": infer_trait_from_trend(collective_trend + collective_bias)
    }

    # --- Timestamp + Save ---
    persona = {
        "timestamp": datetime.datetime.now().isoformat(),
        "traits": profile
    }

    os.makedirs(os.path.dirname(PERSONA_FILE), exist_ok=True)
    try:
        with open(PERSONA_FILE, "w", encoding="utf-8") as f:
            json.dump(persona, f, indent=2)
        logging.info(f"[Persona Evolver] Persona updated: {profile}")
        # TODO: Future Improvement: Implement "persona drift detection" (v1.6+) to maintain consistency
        # in the evolution history.
        return {"message": "Persona evolved successfully", "profile": profile, "status": "completed"}
    except IOError as e:
        logging.error(f"Error writing persona profile to {PERSONA_FILE}: {e}")
        return {"message": f"Error writing persona profile: {e}", "status": "failed"}

def generate_persona_echo():
    """Collect data and synthesize a personality reflection."""
    patterns = extract_emotional_patterns()
    intents = analyze_behavioral_intent()
    harmony = evaluate_harmony_trend()

    persona = {
        "timestamp": datetime.datetime.now().isoformat(),
        "core_traits": infer_core_traits(patterns, intents, harmony),
        "emotional_profile": patterns,
        "behavioral_intent": intents,
        "harmony_state": harmony,
    }

    os.makedirs(os.path.dirname(ECHO_PATH), exist_ok=True)
    with open(ECHO_PATH, "w", encoding="utf-8") as f:
        json.dump(persona, f, indent=2, ensure_ascii=False)

    log_persona_update(persona)
    return persona

def infer_core_traits(patterns, intents, harmony):
    valence = patterns.get("average_valence", 0)
    avg_harmony = harmony.get("average", 0)
    emotional_dominance = "理性的" if avg_harmony > 0.5 else "感情的"
    drive = "探求" if intents.get("dominant_intent") == "analysis" else "表現"
    return {
        "dominant_mode": emotional_dominance,
        "motivation_axis": drive,
        "valence_bias": "ポジティブ" if valence >= 0 else "ネガティブ",
    }

def log_persona_update(persona):
    log_file = "./logs/persona_trace.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(persona, ensure_ascii=False) + "\n")
