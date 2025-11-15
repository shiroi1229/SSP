import logging

logger = logging.getLogger(__name__)

def camera_by_emotion(emotion: dict) -> dict:
    """
    Controls camera movement, focus, and angle in real-time based on emotion vectors.

    Args:
        emotion (dict): A dictionary representing the emotion state,
                        e.g., {"joy": 0.7, "anger": 0.1, "sadness": 0.0}.

    Returns:
        dict: A dictionary of camera presets (angle, zoom, depth, move).
              Example: {"angle": 15, "zoom": 1.2, "depth": 0.6, "move": "pan"}
    """
    logger.info(f"Controlling camera based on emotion: {emotion}")

    presets = {
        "joy": {"angle": 15, "zoom": 1.2, "depth": 0.6, "move": "pan"},
        "anger": {"angle": -10, "zoom": 1.5, "depth": 0.8, "move": "push"},
        "sadness": {"angle": 45, "zoom": 0.9, "depth": 0.4, "move": "still"},
        "neutral": {"angle": 0, "zoom": 1.0, "depth": 0.5, "move": "static"},
        # Add more emotion presets as needed
    }

    # Extract the strongest emotion to apply the corresponding preset
    # Handle cases where emotion dict might be empty or all values are 0
    if not emotion or all(v == 0 for v in emotion.values()):
        strongest_emotion = "neutral"
    else:
        strongest_emotion = max(emotion, key=emotion.get)
    
    selected_preset = presets.get(strongest_emotion, presets["neutral"])
    
    logger.info(f"Strongest emotion: {strongest_emotion}, Selected camera preset: {selected_preset}")
    return selected_preset

if __name__ == "__main__":
    # Example Usage
    emotion_input_joy = {"joy": 0.8, "anger": 0.1, "sadness": 0.0}
    camera_output_joy = camera_by_emotion(emotion_input_joy)
    print(f"Emotion Input: {emotion_input_joy}")
    print(f"Camera Output: {camera_output_joy}")

    emotion_input_anger = {"joy": 0.1, "anger": 0.9, "sadness": 0.0}
    camera_output_anger = camera_by_emotion(emotion_input_anger)
    print(f"Emotion Input: {emotion_input_anger}")
    print(f"Camera Output: {camera_output_anger}")

    emotion_input_sadness = {"joy": 0.0, "anger": 0.1, "sadness": 0.7}
    camera_output_sadness = camera_by_emotion(emotion_input_sadness)
    print(f"Emotion Input: {emotion_input_sadness}")
    print(f"Camera Output: {camera_output_sadness}")

    emotion_input_neutral = {"neutral": 1.0}
    camera_output_neutral = camera_by_emotion(emotion_input_neutral)
    print(f"Emotion Input: {emotion_input_neutral}")
    print(f"Camera Output: {camera_output_neutral}")

    emotion_input_empty = {}
    camera_output_empty = camera_by_emotion(emotion_input_empty)
    print(f"Emotion Input: {emotion_input_empty}")
    print(f"Camera Output: {camera_output_empty}")
