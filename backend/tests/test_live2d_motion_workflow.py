import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from orchestrator.workflow import run_live2d_motion_workflow
from modules.motion_translator import emotion_to_motion
from modules.adaptive_physics import update_physics
from modules.smooth_transition_generator import generate_smooth_motion_transition
from modules.auto_pose_correction import auto_pose_correction

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.motion_translator.logger', MagicMock()) as mock_mt_logger, \
         patch('modules.adaptive_physics.logger', MagicMock()) as mock_ap_logger, \
         patch('modules.smooth_transition_generator.logger', MagicMock()) as mock_stg_logger, \
         patch('modules.auto_pose_correction.logger', MagicMock()) as mock_apc_logger, \
         patch('orchestrator.workflow.log_manager', MagicMock()) as mock_wf_logger:
        yield

def test_run_live2d_motion_workflow_joyful_expression():
    """
    Tests the Live2D motion workflow with a joyful emotion input.
    """
    emotion_input = {"joy": 0.8, "neutral": 0.2}
    current_live2d_params = {
        "eyeOpen": 0.5, "mouthForm": 0.0, "browY": 0.0,
        "paramAngleX": 0.0, "paramMouthOpenY": 0.0,
        "gravity_y": 0.5, "resistance": 0.8
    }
    emotion_harmony = 0.7
    delta_time = 0.016

    # Expected outputs (simplified for testing, actual values depend on module logic)
    # These should ideally be calculated based on the exact logic in the modules
    # For now, we'll use approximate expected values.

    # Expected from emotion_to_motion (joy: 0.8, neutral: 0.2)
    # joy: {"eyeOpen": 1.0, "mouthForm": 0.8, "browY": 0.5, "paramAngleX": 0.3, "paramMouthOpenY": 0.7}
    # neutral: {"eyeOpen": 0.8, "mouthForm": 0.0, "browY": 0.0, "paramAngleX": 0.0, "paramMouthOpenY": 0.5}
    # Combined (simplified sum for test expectation):
    # eyeOpen: 0.8*1.0 + 0.2*0.8 = 0.8 + 0.16 = 0.96
    # mouthForm: 0.8*0.8 + 0.2*0.0 = 0.64
    # browY: 0.8*0.5 + 0.2*0.0 = 0.4
    # paramAngleX: 0.8*0.3 + 0.2*0.0 = 0.24
    # paramMouthOpenY: 0.8*0.7 + 0.2*0.5 = 0.56 + 0.1 = 0.66
    expected_target_motion = {
        "eyeOpen": 0.96, "mouthForm": 0.64, "browY": 0.4,
        "paramAngleX": 0.24, "paramMouthOpenY": 0.66
    }

    # Expected from generate_smooth_motion_transition (speed=0.3)
    # current: 0.5, target: 0.96 => 0.5 + (0.96 - 0.5) * 0.3 = 0.5 + 0.46 * 0.3 = 0.5 + 0.138 = 0.638
    # current: 0.0, target: 0.64 => 0.0 + (0.64 - 0.0) * 0.3 = 0.192
    # current: 0.0, target: 0.4 => 0.0 + (0.4 - 0.0) * 0.3 = 0.12
    # current: 0.0, target: 0.24 => 0.0 + (0.24 - 0.0) * 0.3 = 0.072
    # current: 0.0, target: 0.66 => 0.0 + (0.66 - 0.0) * 0.3 = 0.198
    expected_transitioned_params = {
        "eyeOpen": 0.638, "mouthForm": 0.192, "browY": 0.12,
        "paramAngleX": 0.072, "paramMouthOpenY": 0.198
    }

    # Expected from update_physics (harmony=0.7)
    # gravity_y = lerp(0.6, 0.3, 0.7) = 0.6 + (0.3 - 0.6) * 0.7 = 0.6 - 0.3 * 0.7 = 0.6 - 0.21 = 0.39
    # resistance = lerp(0.9, 0.7, 0.7) = 0.9 + (0.7 - 0.9) * 0.7 = 0.9 - 0.2 * 0.7 = 0.9 - 0.14 = 0.76
    expected_updated_physics = {
        "gravity_y": 0.39,
        "resistance": 0.76,
    }

    # Expected from auto_pose_correction (confidence=0.8)
    # correction_strength = 1.0 - 0.8 = 0.2
    # For eyeOpen: 0.638 + (0.96 - 0.638) * 0.2 = 0.638 + 0.322 * 0.2 = 0.638 + 0.0644 = 0.7024
    # For mouthForm: 0.192 + (0.64 - 0.192) * 0.2 = 0.192 + 0.448 * 0.2 = 0.192 + 0.0896 = 0.2816
    # For browY: 0.12 + (0.4 - 0.12) * 0.2 = 0.12 + 0.28 * 0.2 = 0.12 + 0.056 = 0.176
    # For paramAngleX: 0.072 + (0.24 - 0.072) * 0.2 = 0.072 + 0.168 * 0.2 = 0.072 + 0.0336 = 0.1056
    # For paramMouthOpenY: 0.198 + (0.66 - 0.198) * 0.2 = 0.198 + 0.462 * 0.2 = 0.198 + 0.0924 = 0.2904
    expected_final_params = {
        "eyeOpen": pytest.approx(0.7024),
        "mouthForm": pytest.approx(0.2816),
        "browY": pytest.approx(0.176),
        "paramAngleX": pytest.approx(0.1056),
        "paramMouthOpenY": pytest.approx(0.2904)
    }

    final_output = run_live2d_motion_workflow(emotion_input, current_live2d_params, emotion_harmony, delta_time)

    # Assertions
    for param, expected_value in expected_final_params.items():
        assert param in final_output
        assert final_output[param] == expected_value

    # Verify that physics updates are part of the process, even if not directly in final_output
    # (as per current workflow design, physics updates are logged but not returned in final_output)
    # This part would need adjustment if physics directly modifies motion params in the workflow.
    # For now, we just check that the workflow ran without error and produced expected motion params.
    
def test_run_live2d_motion_workflow_sad_expression():
    """
    Tests the Live2D motion workflow with a sad emotion input.
    """
    emotion_input = {"sadness": 0.9}
    current_live2d_params = {
        "eyeOpen": 0.8, "mouthForm": 0.5, "browY": 0.2,
        "paramAngleX": 0.1, "paramMouthOpenY": 0.6,
        "gravity_y": 0.4, "resistance": 0.7
    }
    emotion_harmony = 0.3
    delta_time = 0.016

    # Expected from emotion_to_motion (sadness: 0.9)
    # eyeOpen: 0.9*0.3 = 0.27
    # mouthForm: 0.9*(-0.4) = -0.36
    # browY: 0.9*(-0.6) = -0.54
    # paramAngleX: 0.9*(-0.2) = -0.18
    # paramMouthOpenY: 0.9*0.2 = 0.18
    expected_target_motion = {
        "eyeOpen": 0.27, "mouthForm": -0.36, "browY": -0.54,
        "paramAngleX": -0.18, "paramMouthOpenY": 0.18
    }

    # Expected from generate_smooth_motion_transition (speed=0.3)
    # current: 0.8, target: 0.27 => 0.8 + (0.27 - 0.8) * 0.3 = 0.8 - 0.53 * 0.3 = 0.8 - 0.159 = 0.641
    # current: 0.5, target: -0.36 => 0.5 + (-0.36 - 0.5) * 0.3 = 0.5 - 0.86 * 0.3 = 0.5 - 0.258 = 0.242
    # current: 0.2, target: -0.54 => 0.2 + (-0.54 - 0.2) * 0.3 = 0.2 - 0.74 * 0.3 = 0.2 - 0.222 = -0.022
    # current: 0.1, target: -0.18 => 0.1 + (-0.18 - 0.1) * 0.3 = 0.1 - 0.28 * 0.3 = 0.1 - 0.084 = 0.016
    # current: 0.6, target: 0.18 => 0.6 + (0.18 - 0.6) * 0.3 = 0.6 - 0.42 * 0.3 = 0.6 - 0.126 = 0.474
    expected_transitioned_params = {
        "eyeOpen": 0.641, "mouthForm": 0.242, "browY": -0.022,
        "paramAngleX": 0.016, "paramMouthOpenY": 0.474
    }

    # Expected from auto_pose_correction (confidence=0.8)
    # correction_strength = 1.0 - 0.8 = 0.2
    # For eyeOpen: 0.641 + (0.27 - 0.641) * 0.2 = 0.641 - 0.371 * 0.2 = 0.641 - 0.0742 = 0.5668
    # For mouthForm: 0.242 + (-0.36 - 0.242) * 0.2 = 0.242 - 0.602 * 0.2 = 0.242 - 0.1204 = 0.1216
    # For browY: -0.022 + (-0.54 - (-0.022)) * 0.2 = -0.022 - 0.518 * 0.2 = -0.022 - 0.1036 = -0.1256
    # For paramAngleX: 0.016 + (-0.18 - 0.016) * 0.2 = 0.016 - 0.196 * 0.2 = 0.016 - 0.0392 = -0.0232
    # For paramMouthOpenY: 0.474 + (0.18 - 0.474) * 0.2 = 0.474 - 0.294 * 0.2 = 0.474 - 0.0588 = 0.4152
    expected_final_params = {
        "eyeOpen": pytest.approx(0.5668),
        "mouthForm": pytest.approx(0.1216),
        "browY": pytest.approx(-0.1256),
        "paramAngleX": pytest.approx(-0.0232),
        "paramMouthOpenY": pytest.approx(0.4152)
    }

    final_output = run_live2d_motion_workflow(emotion_input, current_live2d_params, emotion_harmony, delta_time)

    # Assertions
    for param, expected_value in expected_final_params.items():
        assert param in final_output
        assert final_output[param] == expected_value
