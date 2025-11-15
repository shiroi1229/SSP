import pytest
import sys
import os
import hashlib
import json
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.render_cache_controller import get_cached_render, store_render_cache, clear_render_cache, _render_cache

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.render_cache_controller.logger', MagicMock()) as mock_rcc_logger:
        yield

# Fixture to clear cache before each test
@pytest.fixture(autouse=True)
def setup_teardown_cache():
    clear_render_cache()
    yield
    clear_render_cache()

def _generate_test_hash(data: dict) -> str:
    return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()

def test_cache_miss_and_store():
    scene_id = "scene_1"
    emotion_hash = _generate_test_hash({"joy": 0.8})
    lighting_profile = "day"
    render_result = "render_output_1.mp4"

    # Initial miss
    cached = get_cached_render(scene_id, emotion_hash, lighting_profile)
    assert cached is None

    # Store
    store_render_cache(scene_id, emotion_hash, lighting_profile, render_result)
    # Assert that it can now be retrieved
    cached = get_cached_render(scene_id, emotion_hash, lighting_profile)
    assert cached == render_result

def test_cache_hit_with_same_parameters():
    scene_id = "scene_2"
    emotion_hash = _generate_test_hash({"anger": 0.9})
    lighting_profile = "night"
    render_result_1 = "render_output_2_v1.mp4"
    render_result_2 = "render_output_2_v2.mp4"

    store_render_cache(scene_id, emotion_hash, lighting_profile, render_result_1)
    cached = get_cached_render(scene_id, emotion_hash, lighting_profile)
    assert cached == render_result_1

    # Storing again with same key should overwrite
    store_render_cache(scene_id, emotion_hash, lighting_profile, render_result_2)
    cached = get_cached_render(scene_id, emotion_hash, lighting_profile)
    assert cached == render_result_2

def test_cache_miss_with_different_parameters():
    scene_id_1 = "scene_3"
    emotion_hash_1 = _generate_test_hash({"sadness": 0.7})
    lighting_profile_1 = "dawn"
    render_result_1 = "render_output_3.mp4"

    scene_id_2 = "scene_4"
    emotion_hash_2 = _generate_test_hash({"joy": 0.5})
    lighting_profile_2 = "dusk"
    render_result_2 = "render_output_4.mp4"

    store_render_cache(scene_id_1, emotion_hash_1, lighting_profile_1, render_result_1)

    # Different scene_id
    cached = get_cached_render(scene_id_2, emotion_hash_1, lighting_profile_1)
    assert cached is None

    # Different emotion_hash
    cached = get_cached_render(scene_id_1, emotion_hash_2, lighting_profile_1)
    assert cached is None

    # Different lighting_profile
    cached = get_cached_render(scene_id_1, emotion_hash_1, lighting_profile_2)
    assert cached is None

def test_clear_render_cache():
    scene_id = "scene_5"
    emotion_hash = _generate_test_hash({"neutral": 1.0})
    lighting_profile = "indoor"
    render_result = "render_output_5.mp4"

    store_render_cache(scene_id, emotion_hash, lighting_profile, render_result)
    assert get_cached_render(scene_id, emotion_hash, lighting_profile) == render_result

    clear_render_cache()
    assert _render_cache == {}
    assert get_cached_render(scene_id, emotion_hash, lighting_profile) is None

def test_cache_key_generation_consistency():
    params1 = ("scene_A", _generate_test_hash({"joy": 0.5}), "light_X")
    params2 = ("scene_A", _generate_test_hash({"joy": 0.5}), "light_X")
    
    store_render_cache(*params1, "result_A")
    cached = get_cached_render(*params2)
    assert cached == "result_A"

    params3 = ("scene_A", _generate_test_hash({"joy": 0.6}), "light_X") # Different emotion
    cached = get_cached_render(*params3)
    assert cached is None
