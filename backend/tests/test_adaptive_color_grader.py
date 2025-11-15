import pytest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.adaptive_color_grader import adaptive_color_grade

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.adaptive_color_grader.logger', MagicMock()) as mock_acg_logger:
        yield

# Helper function to create a dummy frame
def create_dummy_frame(color=(128, 128, 128), size=(10, 10)):
    frame = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    frame[:, :, 0] = color[0]
    frame[:, :, 1] = color[1]
    frame[:, :, 2] = color[2]
    return frame

def test_adaptive_color_grade_joy():
    frame = create_dummy_frame(color=(128, 128, 128)) # Grey frame
    emotion_input = {"joy": 0.8}
    
    graded_frame = adaptive_color_grade(frame, emotion_input)
    
    # Expect red channel to increase, blue to decrease for joyful (warm)
    assert graded_frame[0, 0, 0] > frame[0, 0, 0] # Red should increase
    assert graded_frame[0, 0, 2] < frame[0, 0, 2] # Blue should decrease
    # Green should remain relatively similar or slightly change due to normalization/clipping
    assert graded_frame[0, 0, 1] == pytest.approx(frame[0, 0, 1], abs=5) # Allow small deviation

def test_adaptive_color_grade_sadness():
    frame = create_dummy_frame(color=(128, 128, 128)) # Grey frame
    emotion_input = {"sadness": 0.7}
    
    graded_frame = adaptive_color_grade(frame, emotion_input)
    
    # Expect blue channel to increase, red to decrease for sadness (cold)
    assert graded_frame[0, 0, 2] > frame[0, 0, 2] # Blue should increase
    assert graded_frame[0, 0, 0] < frame[0, 0, 0] # Red should decrease
    assert graded_frame[0, 0, 1] == pytest.approx(frame[0, 0, 1], abs=5)

def test_adaptive_color_grade_anger():
    frame = create_dummy_frame(color=(128, 128, 128)) # Grey frame
    emotion_input = {"anger": 0.9}
    
    graded_frame = adaptive_color_grade(frame, emotion_input)
    
    # Expect red channel to increase significantly, green and blue to decrease
    assert graded_frame[0, 0, 0] > frame[0, 0, 0] # Red should increase
    assert graded_frame[0, 0, 1] < frame[0, 0, 1] # Green should decrease
    assert graded_frame[0, 0, 2] < frame[0, 0, 2] # Blue should decrease

def test_adaptive_color_grade_neutral_no_change():
    frame = create_dummy_frame(color=(128, 128, 128)) # Grey frame
    emotion_input = {"neutral": 1.0}
    
    graded_frame = adaptive_color_grade(frame, emotion_input)
    
    # Neutral emotion with no specific lighting info should result in minimal change
    # The current implementation has a default neutral, but no specific color shift.
    # So, it should be very close to the original.
    assert np.allclose(graded_frame, frame, atol=1) # Allow for minor floating point differences

def test_adaptive_color_grade_lighting_warm():
    frame = create_dummy_frame(color=(128, 128, 128))
    emotion_input = {"neutral": 1.0}
    lighting_info = {"temperature": "warm"}
    
    graded_frame = adaptive_color_grade(frame, emotion_input, lighting_info)
    
    # Expect red channel to increase due to warm lighting
    assert graded_frame[0, 0, 0] > frame[0, 0, 0]
    assert graded_frame[0, 0, 1] == pytest.approx(frame[0, 0, 1], abs=5)
    assert graded_frame[0, 0, 2] == pytest.approx(frame[0, 0, 2], abs=5)

def test_adaptive_color_grade_lighting_cold():
    frame = create_dummy_frame(color=(128, 128, 128))
    emotion_input = {"neutral": 1.0}
    lighting_info = {"temperature": "cold"}
    
    graded_frame = adaptive_color_grade(frame, emotion_input, lighting_info)
    
    # Expect blue channel to increase due to cold lighting
    assert graded_frame[0, 0, 2] > frame[0, 0, 2]
    assert graded_frame[0, 0, 0] == pytest.approx(frame[0, 0, 0], abs=5)
    assert graded_frame[0, 0, 1] == pytest.approx(frame[0, 0, 1], abs=5)

def test_adaptive_color_grade_brightness_adjustment():
    frame = create_dummy_frame(color=(128, 128, 128))
    emotion_input = {"neutral": 1.0}
    lighting_info = {"brightness": 1.2} # Brighter
    
    graded_frame = adaptive_color_grade(frame, emotion_input, lighting_info)
    
    # Expect all channels to increase
    assert graded_frame[0, 0, 0] > frame[0, 0, 0]
    assert graded_frame[0, 0, 1] > frame[0, 0, 1]
    assert graded_frame[0, 0, 2] > frame[0, 0, 2]

    lighting_info_darker = {"brightness": 0.8} # Darker
    graded_frame_darker = adaptive_color_grade(frame, emotion_input, lighting_info_darker)
    
    # Expect all channels to decrease
    assert graded_frame_darker[0, 0, 0] < frame[0, 0, 0]
    assert graded_frame_darker[0, 0, 1] < frame[0, 0, 1]
    assert graded_frame_darker[0, 0, 2] < frame[0, 0, 2]
