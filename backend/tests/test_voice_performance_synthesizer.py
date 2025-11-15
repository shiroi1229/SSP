import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.voice_performance_synthesizer import synthesize_performance

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.voice_performance_synthesizer.logger', MagicMock()) as mock_vps_logger:
        yield

def test_synthesize_performance_joyful():
    text_content = "Hello there!"
    emotion_vector = {"joy": 0.8, "neutral": 0.2}
    scene_context = {"scene_type": "studio", "lighting": "bright"}
    
    result = synthesize_performance(text_content, emotion_vector, scene_context)
    
    assert isinstance(result, str)
    assert "simulated_audio_for_Hello_ther" in result # Check for text content in filename
    assert "_p1.24_t1.0_tonebright" in result # Check for modulated params
    assert "_decay0.2_wet0.1" in result # Check for IR params

def test_synthesize_performance_sad():
    text_content = "Goodbye for now."
    emotion_vector = {"sadness": 0.7, "neutral": 0.3}
    scene_context = {"scene_type": "hall"}
    
    result = synthesize_performance(text_content, emotion_vector, scene_context)
    
    assert isinstance(result, str)
    assert "simulated_audio_for_Goodbye_fo" in result
    assert "_p0.86_t1.0_tonesoft" in result # pitch = 1.0 - 0.7*0.2 = 0.86, tone=soft
    assert "_decay1.2_wet0.5" in result # hall IR

def test_synthesize_performance_with_pauses():
    text_content = "Wait... for me."
    emotion_vector = {"neutral": 1.0}
    scene_context = {"scene_type": "studio"}
    pause_info = [{"start": 0.5, "duration": 0.2}, {"start": 1.0, "duration": 0.5}]
    
    result = synthesize_performance(text_content, emotion_vector, scene_context, pause_info)
    
    assert isinstance(result, str)
    assert "_pause_s0.5_d0.2" in result
    assert "_pause_s1.0_d0.5" in result

def test_synthesize_performance_empty_emotion():
    text_content = "Just speaking."
    emotion_vector = {}
    scene_context = {"scene_type": "studio"}
    
    result = synthesize_performance(text_content, emotion_vector, scene_context)
    
    assert isinstance(result, str)
    assert "_p1.0_t1.0_toneneutral" in result # Default neutral params

def test_synthesize_performance_unknown_scene_type():
    text_content = "In a strange place."
    emotion_vector = {"neutral": 1.0}
    scene_context = {"scene_type": "unknown_location"}
    
    result = synthesize_performance(text_content, emotion_vector, scene_context)
    
    assert isinstance(result, str)
    assert "_decay0.2_wet0.1" in result # Should default to studio IR
