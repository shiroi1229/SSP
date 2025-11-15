import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.stereo_depth_enhancer import stereo_depth, apply_binaural_effect

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.stereo_depth_enhancer.logger', MagicMock()) as mock_sde_logger:
        yield

def test_stereo_depth_joy():
    audio_data = "raw_audio_segment"
    emotion_input = {"joy": 0.8, "anger": 0.1, "sadness": 0.0}
    
    # pan = 0.3 * 0.8 - 0.2 * 0.1 = 0.24 - 0.02 = 0.22
    # depth = 1.0 - 0.0 * 0.5 = 1.0
    expected_output = apply_binaural_effect(audio_data, 0.22, 1.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output

def test_stereo_depth_anger():
    audio_data = "raw_audio_segment"
    emotion_input = {"joy": 0.1, "anger": 0.9, "sadness": 0.0}
    
    # pan = 0.3 * 0.1 - 0.2 * 0.9 = 0.03 - 0.18 = -0.15
    # depth = 1.0 - 0.0 * 0.5 = 1.0
    expected_output = apply_binaural_effect(audio_data, -0.15, 1.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output

def test_stereo_depth_sadness():
    audio_data = "raw_audio_segment"
    emotion_input = {"joy": 0.0, "anger": 0.1, "sadness": 0.7}
    
    # pan = 0.3 * 0.0 - 0.2 * 0.1 = -0.02
    # depth = 1.0 - 0.7 * 0.5 = 1.0 - 0.35 = 0.65
    expected_output = apply_binaural_effect(audio_data, -0.02, 0.65)
    assert stereo_depth(audio_data, emotion_input) == expected_output

def test_stereo_depth_neutral():
    audio_data = "raw_audio_segment"
    emotion_input = {"neutral": 1.0}
    
    # pan = 0.0 (since joy and anger are 0)
    # depth = 1.0 (since sadness is 0)
    expected_output = apply_binaural_effect(audio_data, 0.0, 1.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output

def test_stereo_depth_empty_emotion():
    audio_data = "raw_audio_segment"
    emotion_input = {}
    
    # pan = 0.0
    # depth = 1.0
    expected_output = apply_binaural_effect(audio_data, 0.0, 1.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output

def test_stereo_depth_clamping_pan():
    audio_data = "raw_audio_segment"
    emotion_input = {"joy": 2.0, "anger": 0.0, "sadness": 0.0} # Extreme joy
    
    # pan = 0.3 * 2.0 - 0.2 * 0.0 = 0.6 (within -1 to 1)
    # depth = 1.0
    expected_output = apply_binaural_effect(audio_data, 0.6, 1.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output

    emotion_input_extreme_anger = {"joy": 0.0, "anger": 3.0, "sadness": 0.0} # Extreme anger
    # pan = 0.3 * 0.0 - 0.2 * 3.0 = -0.6 (within -1 to 1)
    # depth = 1.0
    expected_output_extreme_anger = apply_binaural_effect(audio_data, -0.6, 1.0)
    assert stereo_depth(audio_data, emotion_input_extreme_anger) == expected_output_extreme_anger

def test_stereo_depth_clamping_depth():
    audio_data = "raw_audio_segment"
    emotion_input = {"joy": 0.0, "anger": 0.0, "sadness": 3.0} # Extreme sadness
    
    # pan = 0.0
    # depth = 1.0 - 3.0 * 0.5 = 1.0 - 1.5 = -0.5 (clamped to 0.0)
    expected_output = apply_binaural_effect(audio_data, 0.0, 0.0)
    assert stereo_depth(audio_data, emotion_input) == expected_output
