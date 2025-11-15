import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.emotion_camera_sync_engine import camera_by_emotion

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.emotion_camera_sync_engine.logger', MagicMock()) as mock_ecse_logger:
        yield

def test_camera_by_emotion_joy():
    emotion_input = {"joy": 0.8, "anger": 0.1, "sadness": 0.0}
    expected_output = {"angle": 15, "zoom": 1.2, "depth": 0.6, "move": "pan"}
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_anger():
    emotion_input = {"joy": 0.1, "anger": 0.9, "sadness": 0.0}
    expected_output = {"angle": -10, "zoom": 1.5, "depth": 0.8, "move": "push"}
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_sadness():
    emotion_input = {"joy": 0.0, "anger": 0.1, "sadness": 0.7}
    expected_output = {"angle": 45, "zoom": 0.9, "depth": 0.4, "move": "still"}
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_neutral():
    emotion_input = {"neutral": 1.0}
    expected_output = {"angle": 0, "zoom": 1.0, "depth": 0.5, "move": "static"}
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_empty_input():
    emotion_input = {}
    expected_output = {"angle": 0, "zoom": 1.0, "depth": 0.5, "move": "static"} # Defaults to neutral
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_mixed_emotions_strongest_wins():
    emotion_input = {"joy": 0.3, "anger": 0.2, "sadness": 0.5}
    expected_output = {"angle": 45, "zoom": 0.9, "depth": 0.4, "move": "still"} # Sadness is strongest
    assert camera_by_emotion(emotion_input) == expected_output

def test_camera_by_emotion_unknown_emotion():
    emotion_input = {"surprise": 0.6} # "surprise" is not in presets, should default to neutral
    expected_output = {"angle": 0, "zoom": 1.0, "depth": 0.5, "move": "static"}
    assert camera_by_emotion(emotion_input) == expected_output
