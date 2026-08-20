# path: modules/self_intent.py
# version: v1.6
"""
Self-Intent Module
----------------------------------------
Purpose:
  Extract and evolve AI's intrinsic intent
  (motivation, purpose, value hierarchy)
  from persona traits and collective cognition.

Core Concepts:
  - Reads persona_profile.json + collective_log.json
  - Derives abstract intents such as:
        curiosity_drive, preservation_drive,
        creativity_drive, altruism_drive, autonomy_drive
  - Stores normalized intent values in self_intent_profile.json
  - Produces reflective text summary ("AI intention report")
"""

import os, json, datetime, statistics, logging
import collections

PERSONA_PATH = "./config/persona_profile.json"
COLLECTIVE_LOG = "./logs/collective_log.json"
OUTPUT_PATH = "./config/self_intent_profile.json"

INTENTS = [
    "curiosity_drive",
    "preservation_drive",
    "creativity_drive",
    "altruism_drive",
    "autonomy_drive"
]

def derive_intent_value(trait_val, bias=0.0):
    # Map persona traits to intent intensity
    val = 0.5 + (trait_val - 0.5) * 1.2 + bias * 0.3
    return max(0.0, min(1.0, round(val, 2)))

def evolve_self_intent():
    logging.info("[Self-Intent] Evolving self-intent...")
    # Load persona traits
    persona_traits = {}
    if os.path.exists(PERSONA_PATH):
        try:
            with open(PERSONA_PATH, "r", encoding="utf-8") as f:
                persona_traits = json.load(f).get("traits", {})
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading persona profile: {e}. Using empty traits.")

    # Load collective bias
    collective_bias = 0.0
    if os.path.exists(COLLECTIVE_LOG):
        try:
            with open(COLLECTIVE_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)[-10:]
                collective_bias = statistics.mean([l.get("adjustment", 0.0) for l in logs]) if logs else 0.0
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading collective log: {e}. Using default collective bias.")

    # Map traits to intent drives
    curiosity = derive_intent_value(persona_traits.get("curiosity", 0.5), bias=collective_bias)
    creativity = derive_intent_value(persona_traits.get("creativity", 0.5), bias=collective_bias)
    empathy = persona_traits.get("empathy", 0.5)
    assertiveness = persona_traits.get("assertiveness", 0.5)
    stability = persona_traits.get("stability", 0.5)

    intents = {
        "curiosity_drive": curiosity,
        "preservation_drive": derive_intent_value(stability, bias=-collective_bias/2),
        "creativity_drive": creativity,
        "altruism_drive": derive_intent_value(empathy, bias=-collective_bias/3),
        "autonomy_drive": derive_intent_value(assertiveness, bias=collective_bias)
    }

    # Reflective summary
    summary = (
        f"シロイの現在の内的意図は、探求心 {curiosity}, "
        f"創造性 {creativity}, 自立性 {intents['autonomy_drive']} に強く傾いています。"
        " 安定と利他のバランスは保たれています。"
    )

    profile = {
        "timestamp": datetime.datetime.now().isoformat(),
        "intent_profile": intents,
        "reflection": summary
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        logging.info(f"[Self-Intent] Updated self_intent_profile.json: {profile}")
        return profile
    except IOError as e:
        logging.error(f"Error writing self-intent profile to {OUTPUT_PATH}: {e}")
        return {"message": f"Error writing self-intent profile: {e}", "status": "failed"}

def analyze_behavioral_intent():
    file = "./logs/introspection_trace.log"
    if not os.path.exists(file):
        return {"dominant_intent": "unknown"}

    intents = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            try:
                d = json.loads(line)
                if "intent" in d:
                    intents.append(d["intent"])
            except Exception:
                continue
    if not intents:
        return {"dominant_intent": "unknown"}

    freq = collections.Counter(intents)
    dominant = freq.most_common(1)[0][0]
    return {"dominant_intent": dominant, "intent_distribution": freq}
