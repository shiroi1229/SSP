import logging
import numpy as np

logger = logging.getLogger(__name__)

def adaptive_color_grade(frame: np.ndarray, emotion_vector: dict, lighting_info: dict = None) -> np.ndarray:
    """
    Adjusts color properties (hue, saturation, exposure, contrast) of a video frame
    based on lighting information and emotion tags.

    Args:
        frame (np.ndarray): The input video frame as a NumPy array (e.g., RGB or RGBA).
                            Expected shape: (height, width, channels).
        emotion_vector (dict): A dictionary representing the emotion state,
                               e.g., {"joy": 0.7, "anger": 0.1, "sadness": 0.0}.
        lighting_info (dict, optional): Information about the scene's lighting.
                                        Example: {"brightness": 0.8, "temperature": "warm"}.
                                        Defaults to None.

    Returns:
        np.ndarray: The color-corrected video frame.
    """
    logger.info(f"Applying adaptive color grading. Emotion: {emotion_vector}, Lighting: {lighting_info}")

    # Ensure frame is float for calculations
    graded_frame = frame.astype(np.float32) / 255.0 # Normalize to 0-1 range

    # Determine dominant emotion
    dominant_emotion = "neutral"
    if emotion_vector:
        dominant_emotion = max(emotion_vector, key=emotion_vector.get)

    # Simple tone adjustment based on dominant emotion (as per spec example)
    if dominant_emotion == "joy" or (dominant_emotion == "neutral" and emotion_vector.get("joy", 0) > 0.6):
        # Warm tone for joy
        # Increase Red channel slightly
        graded_frame[..., 0] *= 1.05
        # Decrease Blue channel slightly
        graded_frame[..., 2] *= 0.95
    elif dominant_emotion == "sadness" or (dominant_emotion == "neutral" and emotion_vector.get("sadness", 0) > 0.6):
        # Cold tone for sadness
        # Increase Blue channel slightly
        graded_frame[..., 2] *= 1.05
        # Decrease Red channel slightly
        graded_frame[..., 0] *= 0.95
    elif dominant_emotion == "anger" or (dominant_emotion == "neutral" and emotion_vector.get("anger", 0) > 0.6):
        # Intense, slightly reddish tone for anger
        graded_frame[..., 0] *= 1.1 # More red
        graded_frame[..., 1] *= 0.9 # Less green
        graded_frame[..., 2] *= 0.9 # Less blue
    
    # Further adjustments based on lighting_info (placeholder for more complex logic)
    if lighting_info:
        if lighting_info.get("temperature") == "warm":
            graded_frame[..., 0] *= 1.03 # Boost red
        elif lighting_info.get("temperature") == "cold":
            graded_frame[..., 2] *= 1.03 # Boost blue
        
        brightness_factor = lighting_info.get("brightness", 1.0)
        graded_frame *= brightness_factor # Adjust overall brightness

    # Clamp values back to 0-1 range and convert back to uint8
    graded_frame = np.clip(graded_frame, 0.0, 1.0)
    graded_frame = (graded_frame * 255).astype(np.uint8)

    logger.info("Color grading applied.")
    return graded_frame

if __name__ == "__main__":
    # Example Usage: Create a dummy frame (e.g., a 100x100 red square)
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_frame[:, :, 0] = 255 # Red channel full

    print("--- Original Frame (Red) ---")
    # print(dummy_frame[0,0,:]) # Example pixel value

    # Test with joyful emotion
    emotion_joy = {"joy": 0.8}
    graded_joy_frame = adaptive_color_grade(dummy_frame, emotion_joy)
    print(f"\n--- Graded Frame (Joyful Emotion) ---")
    # print(graded_joy_frame[0,0,:]) # Should be more reddish/warm

    # Test with sadness emotion
    emotion_sad = {"sadness": 0.7}
    graded_sad_frame = adaptive_color_grade(dummy_frame, emotion_sad)
    print(f"\n--- Graded Frame (Sadness Emotion) ---")
    # print(graded_sad_frame[0,0,:]) # Should be less reddish/colder

    # Test with anger emotion
    emotion_anger = {"anger": 0.9}
    graded_anger_frame = adaptive_color_grade(dummy_frame, emotion_anger)
    print(f"\n--- Graded Frame (Anger Emotion) ---")
    # print(graded_anger_frame[0,0,:]) # Should be more intense red

    # Test with neutral emotion and warm lighting
    emotion_neutral = {"neutral": 1.0}
    lighting_warm = {"brightness": 1.0, "temperature": "warm"}
    graded_neutral_warm_frame = adaptive_color_grade(dummy_frame, emotion_neutral, lighting_warm)
    print(f"\n--- Graded Frame (Neutral Emotion, Warm Lighting) ---")
    # print(graded_neutral_warm_frame[0,0,:]) # Should be slightly warmer
