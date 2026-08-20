import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.emotion_modulation_network import modulate_voice_params

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.emotion_modulation_network.logger', MagicMock()) as mock_emn_logger:
        yield

def test_modulate_voice_params_joy():
    emotion_input = {"joy": 0.8, "anger": 0.1, "sadness": 0.0}
    expected_params = {"pitch": pytest.approx(1.24), "tempo": pytest.approx(0.99), "tone": "bright"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_anger():
    emotion_input = {"joy": 0.1, "anger": 0.9, "sadness": 0.0}
    expected_params = {"pitch": pytest.approx(1.03), "tempo": pytest.approx(0.91), "tone": "bright"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_sadness():
    emotion_input = {"joy": 0.0, "anger": 0.1, "sadness": 0.7}
    expected_params = {"pitch": pytest.approx(0.86), "tempo": pytest.approx(0.99), "tone": "soft"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_neutral():
    emotion_input = {"neutral": 1.0}
    expected_params = {"pitch": pytest.approx(1.0), "tempo": pytest.approx(1.0), "tone": "neutral"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_mixed_emotions():
    emotion_input = {"joy": 0.4, "anger": 0.3, "sadness": 0.3}
    # pitch = 1.0 + 0.4*0.3 - 0.3*0.2 = 1.0 + 0.12 - 0.06 = 1.06
    # tempo = 1.0 - 0.3*0.1 = 0.97
    # tone = "neutral" (since sadness <= 0.5, joy <= 0.5, anger <= 0.5)
    expected_params = {"pitch": pytest.approx(1.06), "tempo": pytest.approx(0.97), "tone": "neutral"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_empty_input():
    emotion_input = {}
    expected_params = {"pitch": pytest.approx(1.0), "tempo": pytest.approx(1.0), "tone": "neutral"}
    assert modulate_voice_params(emotion_input) == expected_params

def test_modulate_voice_params_clamping():
    emotion_input = {"sadness": 1.0, "joy": 0.0, "anger": 0.0}
    # pitch = 1.0 + 0*0.3 - 1.0*0.2 = 0.8
    # tempo = 1.0 - 0*0.1 = 1.0
    # tone = "soft"
    expected_params = {"pitch": pytest.approx(0.8), "tempo": pytest.approx(1.0), "tone": "soft"}
    assert modulate_voice_params(emotion_input) == expected_params

    emotion_input_extreme_joy = {"joy": 2.0} # Exceeds typical 0-1 range, but function should handle
    # pitch = 1.0 + 2.0*0.3 - 0*0.2 = 1.6
    # tempo = 1.0 - 0*0.1 = 1.0
    # tone = "bright"
    expected_params_extreme_joy = {"pitch": pytest.approx(1.6), "tempo": pytest.approx(1.0), "tone": "bright"}
    assert modulate_voice_params(emotion_input_extreme_joy) == expected_params_extreme_joy
