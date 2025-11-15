import logging

logger = logging.getLogger(__name__)

def emotion_to_motion(emotion_vector: dict) -> dict:
    """
    Translates an emotion vector into Live2D motion parameters.

    Args:
        emotion_vector (dict): A dictionary representing the emotion state,
                               e.g., {"joy": 0.7, "anger": 0.1, "sadness": 0.0}.

    Returns:
        dict: A dictionary of Live2D parameters,
              e.g., {"faceAngle": 0.5, "eyeOpen": 1.0, "mouthForm": 0.8}.
    """
    logger.info(f"Translating emotion vector to motion: {emotion_vector}")

    # Define a mapping from emotion to Live2D parameters
    # These are example mappings and would be refined based on actual Live2D model
    # and desired emotional expressions.
    mapping = {
        "joy": {"eyeOpen": 1.0, "mouthForm": 0.8, "browY": 0.5, "paramAngleX": 0.3, "paramMouthOpenY": 0.7},
        "sadness": {"eyeOpen": 0.3, "mouthForm": -0.4, "browY": -0.6, "paramAngleX": -0.2, "paramMouthOpenY": 0.2},
        "anger": {"eyeOpen": 0.8, "mouthForm": -0.2, "browY": 0.9, "paramAngleX": 0.5, "paramMouthOpenY": 0.4},
        "neutral": {"eyeOpen": 0.8, "mouthForm": 0.0, "browY": 0.0, "paramAngleX": 0.0, "paramMouthOpenY": 0.5},
        # Add more emotions and their corresponding parameter adjustments
    }

    result = {}
    for emotion, intensity in emotion_vector.items():
        if emotion in mapping:
            for param, weight in mapping[emotion].items():
                # Accumulate weighted parameter values
                result[param] = result.get(param, 0.0) + intensity * weight
        else:
            logger.warning(f"Unknown emotion '{emotion}' in emotion vector.")

    # Clamp values to typical Live2D ranges (e.g., -1 to 1 or 0 to 1)
    # This is a simplified clamping; actual ranges depend on the Live2D model
    for param, value in result.items():
        if "eyeOpen" in param or "mouthOpen" in param: # Typically 0 to 1
            result[param] = max(0.0, min(1.0, value))
        else: # Typically -1 to 1
            result[param] = max(-1.0, min(1.0, value))
            
    logger.info(f"Translated motion parameters: {result}")
    return result

if __name__ == "__main__":
    # Example Usage
    emotion_input = {"joy": 0.7, "anger": 0.1, "sadness": 0.0}
    motion_output = emotion_to_motion(emotion_input)
    print(f"Emotion Input: {emotion_input}")
    print(f"Motion Output: {motion_output}")

    emotion_input_sad = {"sadness": 0.9}
    motion_output_sad = emotion_to_motion(emotion_input_sad)
    print(f"Emotion Input: {emotion_input_sad}")
    print(f"Motion Output: {motion_output_sad}")

    emotion_input_neutral = {"neutral": 1.0}
    motion_output_neutral = emotion_to_motion(emotion_input_neutral)
    print(f"Emotion Input: {emotion_input_neutral}")
    print(f"Motion Output: {motion_output_neutral}")
