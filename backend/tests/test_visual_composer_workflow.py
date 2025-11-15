import pytest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from orchestrator.workflow import run_visual_composer_workflow
from modules.emotion_camera_sync_engine import camera_by_emotion
from modules.scene_layout_optimizer import optimize_scene_layout
from modules.adaptive_color_grader import adaptive_color_grade
from modules.render_cache_controller import get_cached_render, store_render_cache, clear_render_cache

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('orchestrator.workflow.log_manager', MagicMock()) as mock_wf_logger, \
         patch('modules.emotion_camera_sync_engine.logger', MagicMock()) as mock_ecse_logger, \
         patch('modules.scene_layout_optimizer.logger', MagicMock()) as mock_slo_logger, \
         patch('modules.adaptive_color_grader.logger', MagicMock()) as mock_acg_logger, \
         patch('modules.render_cache_controller.logger', MagicMock()) as mock_rcc_logger:
        yield

# Fixture to clear cache before each test
@pytest.fixture(autouse=True)
def setup_teardown_cache():
    clear_render_cache()
    yield
    clear_render_cache()

def test_run_visual_composer_workflow_basic_joyful_scene():
    script_json = {
        "title": "Joyful Intro",
        "dialogues": [
            {"speaker": "Shiroi", "text": "Hello world!", "start_time": 0.0, "end_time": 2.0}
        ]
    }
    emotion_vector = {"joy": 0.9, "neutral": 0.1}
    audio_waveform = [{"time": 0.5, "peak": 0.8}]
    lighting_info = {"brightness": 1.0, "temperature": "warm"}
    current_frame = np.zeros((100, 100, 3), dtype=np.uint8) # Dummy frame

    result = run_visual_composer_workflow(script_json, emotion_vector, audio_waveform, lighting_info, current_frame)

    # Assertions for camera preset
    assert result["camera_preset"] == {"angle": 15, "zoom": 1.2, "depth": 0.6, "move": "pan"}

    # Assertions for optimized layout
    assert "optimized_layout" in result
    assert len(result["optimized_layout"]["cuts"]) == 1
    assert result["optimized_layout"]["cuts"][0]["camera_preset"] == "close_up" # Joy > 0.6

    # Assertions for color graded frame (check reference)
    assert "color_graded_frame_ref" in result
    assert result["color_graded_frame_ref"] == "reference_to_color_graded_frame"

    # Assertions for render cache
    assert "render_source" in result
    assert result["render_source"] == "new_render" # Should be a cache miss initially
    assert "final_render_ref" in result
    assert "path/to/rendered/Joyful Intro" in result["final_render_ref"]

    # Test cache hit on second run with same parameters
    result_cached = run_visual_composer_workflow(script_json, emotion_vector, audio_waveform, lighting_info, current_frame)
    assert result_cached["render_source"] == "cache"
    assert result_cached["final_render_ref"] == result["final_render_ref"] # Should retrieve same cached result

def test_run_visual_composer_workflow_sad_scene_with_cache_hit():
    script_json = {
        "title": "Sad Ending",
        "dialogues": [
            {"speaker": "Shiroi", "text": "Goodbye...", "start_time": 0.0, "end_time": 3.0}
        ]
    }
    emotion_vector = {"sadness": 0.8, "neutral": 0.2}
    audio_waveform = [{"time": 1.0, "peak": 0.6}]
    lighting_info = {"brightness": 0.7, "temperature": "cold"}
    current_frame = np.zeros((100, 100, 3), dtype=np.uint8) # Dummy frame

    # First run (cache miss)
    result_first_run = run_visual_composer_workflow(script_json, emotion_vector, audio_waveform, lighting_info, current_frame)
    assert result_first_run["render_source"] == "new_render"
    assert "path/to/rendered/Sad Ending" in result_first_run["final_render_ref"]

    # Second run with same parameters (cache hit expected)
    result_second_run = run_visual_composer_workflow(script_json, emotion_vector, audio_waveform, lighting_info, current_frame)
    assert result_second_run["render_source"] == "cache"
    assert result_second_run["final_render_ref"] == result_first_run["final_render_ref"]

def test_run_visual_composer_workflow_different_emotion_different_cache():
    script_json = {
        "title": "Neutral Scene",
        "dialogues": [
            {"speaker": "Shiroi", "text": "Just a normal day.", "start_time": 0.0, "end_time": 2.5}
        ]
    }
    emotion_vector_neutral = {"neutral": 1.0}
    emotion_vector_happy = {"joy": 0.7}
    audio_waveform = [{"time": 1.0, "peak": 0.3}]
    lighting_info = {"brightness": 0.9, "temperature": "neutral"}
    current_frame = np.zeros((100, 100, 3), dtype=np.uint8) # Dummy frame

    # Run with neutral emotion
    result_neutral = run_visual_composer_workflow(script_json, emotion_vector_neutral, audio_waveform, lighting_info, current_frame)
    assert result_neutral["render_source"] == "new_render"
    
    # Run with happy emotion (should be a new render due to different emotion_hash)
    result_happy = run_visual_composer_workflow(script_json, emotion_vector_happy, audio_waveform, lighting_info, current_frame)
    assert result_happy["render_source"] == "new_render"
    assert result_happy["final_render_ref"] != result_neutral["final_render_ref"] # Different cache key
