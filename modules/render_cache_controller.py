import logging
import hashlib
import json

logger = logging.getLogger(__name__)

# In a real application, this would be a more sophisticated cache (e.g., Redis, disk cache)
# For now, a simple in-memory dictionary will suffice.
_render_cache = {}

def _generate_cache_key(scene_id: str, emotion_hash: str, lighting_profile: str) -> str:
    """
    Generates a unique cache key based on scene parameters.
    """
    key_string = f"{scene_id}_{emotion_hash}_{lighting_profile}"
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()

def get_cached_render(scene_id: str, emotion_hash: str, lighting_profile: str):
    """
    Retrieves a rendered scene from the cache if available.

    Args:
        scene_id (str): Unique identifier for the scene.
        emotion_hash (str): Hash representing the emotion state (e.g., MD5 of emotion vector).
        lighting_profile (str): Identifier for the lighting conditions.

    Returns:
        Any: The cached render result if found, otherwise None.
    """
    cache_key = _generate_cache_key(scene_id, emotion_hash, lighting_profile)
    cached_result = _render_cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for key: {cache_key}")
    else:
        logger.info(f"Cache miss for key: {cache_key}")
    return cached_result

def store_render_cache(scene_id: str, emotion_hash: str, lighting_profile: str, render_result: any):
    """
    Stores a rendered scene result in the cache.

    Args:
        scene_id (str): Unique identifier for the scene.
        emotion_hash (str): Hash representing the emotion state.
        lighting_profile (str): Identifier for the lighting conditions.
        render_result (any): The result of the rendering operation (e.g., file path, binary data).
    """
    cache_key = _generate_cache_key(scene_id, emotion_hash, lighting_profile)
    _render_cache[cache_key] = render_result
    logger.info(f"Stored render result in cache with key: {cache_key}")

def clear_render_cache():
    """
    Clears the entire render cache.
    """
    global _render_cache
    _render_cache = {}
    logger.info("Render cache cleared.")

if __name__ == "__main__":
    # Example Usage
    clear_render_cache()

    scene1_id = "scene_intro"
    emotion1_hash = hashlib.md5(json.dumps({"joy": 0.8}).encode('utf-8')).hexdigest()
    lighting1_profile = "day_bright"
    render1_result = "path/to/render_intro_joy_day.mp4"

    # Test cache miss and store
    cached = get_cached_render(scene1_id, emotion1_hash, lighting1_profile)
    print(f"Initial cache check (miss expected): {cached}")
    store_render_cache(scene1_id, emotion1_hash, lighting1_profile, render1_result)
    cached = get_cached_render(scene1_id, emotion1_hash, lighting1_profile)
    print(f"After storing (hit expected): {cached}")

    # Test another scene/emotion
    scene2_id = "scene_climax"
    emotion2_hash = hashlib.md5(json.dumps({"anger": 0.9}).encode('utf-8')).hexdigest()
    lighting2_profile = "night_stormy"
    render2_result = "path/to/render_climax_anger_night.mp4"

    cached = get_cached_render(scene2_id, emotion2_hash, lighting2_profile)
    print(f"Another scene cache check (miss expected): {cached}")
    store_render_cache(scene2_id, emotion2_hash, lighting2_profile, render2_result)
    cached = get_cached_render(scene2_id, emotion2_hash, lighting2_profile)
    print(f"After storing another scene (hit expected): {cached}")

    # Test cache hit for first scene again
    cached = get_cached_render(scene1_id, emotion1_hash, lighting1_profile)
    print(f"Re-check first scene (hit expected): {cached}")

    clear_render_cache()
    cached = get_cached_render(scene1_id, emotion1_hash, lighting1_profile)
    print(f"After clearing cache (miss expected): {cached}")
