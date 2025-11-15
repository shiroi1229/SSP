import logging

logger = logging.getLogger(__name__)

def modulate_voice_params(emotion_vector: dict) -> dict:
    """
    Analyzes the emotion vector from the Emotion Engine and converts it into
    voice features (pitch, tempo, tone) before text utterance.

    Args:
        emotion_vector (dict): A dictionary representing the emotion state,
                               e.g., {"joy": 0.7, "anger": 0.1, "sadness": 0.0}.

    Returns:
        dict: A dictionary of modulated voice parameters,
              e.g., {"pitch": 1.1, "tempo": 0.9, "tone": "bright"}.
    """
    logger.info(f"Modulating voice parameters based on emotion: {emotion_vector}")

    pitch = 1.0
    tempo = 1.0
    tone = "neutral" # Default tone

    # Apply modulation based on emotion vector, as per specification example
    # pitch: 1.0 + emotion_vector["joy"] * 0.3 - emotion_vector["sadness"] * 0.2
    # tempo: 1.0 - emotion_vector["anger"] * 0.1
    # tone: "soft" if emotion_vector["sadness"] > 0.5 else "bright"

    joy_intensity = emotion_vector.get("joy", 0.0)
    sadness_intensity = emotion_vector.get("sadness", 0.0)
    anger_intensity = emotion_vector.get("anger", 0.0)

    pitch = 1.0 + joy_intensity * 0.3 - sadness_intensity * 0.2
    tempo = 1.0 - anger_intensity * 0.1
    
    if sadness_intensity > 0.5:
        tone = "soft"
    elif joy_intensity > 0.5 or anger_intensity > 0.5: # Assuming bright for strong joy/anger
        tone = "bright"
    else:
        tone = "neutral"

    # Clamp values to reasonable ranges if necessary (e.g., pitch/tempo > 0)
    pitch = max(0.5, min(2.0, pitch)) # Example clamping
    tempo = max(0.5, min(2.0, tempo)) # Example clamping

    modulated_params = {
        "pitch": round(pitch, 2),
        "tempo": round(tempo, 2),
        "tone": tone
    }
    
    logger.info(f"Modulated voice parameters: {modulated_params}")
    return modulated_params

if __name__ == "__main__":
    # Example Usage
    emotion_joy = {"joy": 0.8, "anger": 0.1, "sadness": 0.0}
    params_joy = modulate_voice_params(emotion_joy)
    print(f"Emotion: {emotion_joy}, Modulated Params: {params_joy}")

    emotion_anger = {"joy": 0.1, "anger": 0.9, "sadness": 0.0}
    params_anger = modulate_voice_params(emotion_anger)
    print(f"Emotion: {emotion_anger}, Modulated Params: {params_anger}")

    emotion_sadness = {"joy": 0.0, "anger": 0.1, "sadness": 0.7}
    params_sadness = modulate_voice_params(emotion_sadness)
    print(f"Emotion: {emotion_sadness}, Modulated Params: {params_sadness}")

    emotion_neutral = {"neutral": 1.0}
    params_neutral = modulate_voice_params(emotion_neutral)
    print(f"Emotion: {emotion_neutral}, Modulated Params: {params_neutral}")

    emotion_mixed = {"joy": 0.4, "anger": 0.3, "sadness": 0.3}
    params_mixed = modulate_voice_params(emotion_mixed)
    print(f"Emotion: {emotion_mixed}, Modulated Params: {params_mixed}")
