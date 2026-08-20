import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.scene_layout_optimizer import optimize_scene_layout

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.scene_layout_optimizer.logger', MagicMock()) as mock_slo_logger:
        yield

def test_optimize_scene_layout_basic_dialogue():
    script_json = {
        "title": "Test Scene",
        "dialogues": [
            {"speaker": "A", "text": "Hello.", "start_time": 0.0, "end_time": 1.0},
            {"speaker": "B", "text": "Hi there!", "start_time": 1.5, "end_time": 2.5}
        ]
    }
    audio_waveform = [] # Not used in this basic test
    emotion_vector = {"neutral": 1.0} # Single emotion vector for the scene
    
    expected_cuts = [
        {"start_time": 0.0, "end_time": 1.0, "camera_preset": "medium_shot", "framing": "center", "dialogue_text": "Hello."},
        {"start_time": 1.5, "end_time": 2.5, "camera_preset": "medium_shot", "framing": "center", "dialogue_text": "Hi there!"}
    ]
    
    result = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    assert result["cuts"] == expected_cuts

def test_optimize_scene_layout_strong_emotion_close_up():
    script_json = {
        "title": "Emotional Scene",
        "dialogues": [
            {"speaker": "A", "text": "I'm so happy!", "start_time": 0.0, "end_time": 1.5}
        ]
    }
    audio_waveform = []
    emotion_vector = {"joy": 0.9, "neutral": 0.1} # Single emotion vector for the scene
    
    expected_cuts = [
        {"start_time": 0.0, "end_time": 1.5, "camera_preset": "close_up", "framing": "center", "dialogue_text": "I'm so happy!"}
    ]
    
    result = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    assert result["cuts"] == expected_cuts

def test_optimize_scene_layout_mixed_emotions_strongest_wins():
    script_json = {
        "title": "Mixed Emotion Scene",
        "dialogues": [
            {"speaker": "A", "text": "This is terrible!", "start_time": 0.0, "end_time": 2.0}
        ]
    }
    audio_waveform = []
    emotion_vector = {"joy": 0.3, "anger": 0.7, "sadness": 0.1} # Single emotion vector for the scene
    
    expected_cuts = [
        {"start_time": 0.0, "end_time": 2.0, "camera_preset": "close_up", "framing": "center", "dialogue_text": "This is terrible!"}
    ]
    
    result = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    assert result["cuts"] == expected_cuts

def test_optimize_scene_layout_no_dialogues():
    script_json = {
        "title": "Empty Scene",
        "dialogues": []
    }
    audio_waveform = []
    emotion_vector = {} # Single emotion vector for the scene
    
    expected_cuts = []
    
    result = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    assert result["cuts"] == expected_cuts

def test_optimize_scene_layout_dialogue_without_times():
    script_json = {
        "title": "Untimed Scene",
        "dialogues": [
            {"speaker": "A", "text": "First line."},
            {"speaker": "B", "text": "Second line."}
        ]
    }
    audio_waveform = []
    emotion_vector = {"neutral": 1.0} # Single emotion vector for the scene
    
    # Expected: default start_time 0.0, end_time 2.0, then 2.1 + 2.0 = 4.1
    expected_cuts = [
        {"start_time": 0.0, "end_time": 2.0, "camera_preset": "medium_shot", "framing": "center", "dialogue_text": "First line."},
        {"start_time": 2.1, "end_time": 4.1, "camera_preset": "medium_shot", "framing": "center", "dialogue_text": "Second line."}
    ]
    
    result = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    assert result["cuts"] == expected_cuts
