import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from orchestrator.workflow import run_voice_morph_workflow
from modules.emotion_modulation_network import modulate_voice_params
from modules.scene_acoustic_learner import generate_ir
from modules.voice_performance_synthesizer import synthesize_performance
from modules.stereo_depth_enhancer import stereo_depth

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('orchestrator.workflow.log_manager', MagicMock()) as mock_wf_logger, \
         patch('modules.emotion_modulation_network.logger', MagicMock()) as mock_emn_logger, \
         patch('modules.scene_acoustic_learner.logger', MagicMock()) as mock_sal_logger, \
         patch('modules.voice_performance_synthesizer.logger', MagicMock()) as mock_vps_logger, \
         patch('modules.stereo_depth_enhancer.logger', MagicMock()) as mock_sde_logger:
        yield

def test_run_voice_morph_workflow_joyful_studio():
    text_content = "Hello, everyone! What a wonderful day."
    emotion_vector = {"joy": 0.7, "neutral": 0.3}
    scene_context = {"scene_type": "studio"}
    
    # Expected modulated voice params (from modulate_voice_params)
    # pitch = 1.0 + 0.7*0.3 - 0*0.2 = 1.21
    # tempo = 1.0 - 0*0.1 = 1.0
    # tone = "bright"
    expected_modulated_params = {"pitch": 1.21, "tempo": 1.0, "tone": "bright"}

    # Expected IR params (from generate_ir)
    expected_ir_params = {"decay": 0.2, "wet": 0.1}

    # Expected synthesized audio (from synthesize_performance)
    # This will be a string containing parts of the text, modulated params, and IR params
    # The exact timestamp will vary, so we check for substrings
    expected_vps_output_substrings = [
        "simulated_audio_for_Hello,_eve", # Adjusted for truncation
        f"_p{expected_modulated_params['pitch']}",
        f"_t{expected_modulated_params['tempo']}",
        f"_tone{expected_modulated_params['tone']}",
        f"_decay{expected_ir_params['decay']}",
        f"_wet{expected_ir_params['wet']}"
    ]

    # Expected stereo depth output (from stereo_depth)
    # pan = 0.3 * 0.7 - 0.2 * 0.0 = 0.21
    # depth = 1.0 - 0.0 * 0.5 = 1.0
    expected_sde_pan = 0.21
    expected_sde_depth = 1.0
    expected_sde_output_substrings = [
        "_binaural",
        f"_pan{expected_sde_pan}",
        f"_depth{expected_sde_depth}"
    ]

    result = run_voice_morph_workflow(text_content, emotion_vector, scene_context)

    assert isinstance(result, str)
    for sub in expected_vps_output_substrings:
        assert sub in result
    for sub in expected_sde_output_substrings:
        assert sub in result

def test_run_voice_morph_workflow_sad_hall_with_pauses():
    text_content = "I am... so sorry."
    emotion_vector = {"sadness": 0.9, "neutral": 0.1}
    scene_context = {"scene_type": "hall"}
    pause_info = [{"start": 0.5, "duration": 0.8}]

    # Expected modulated voice params
    # pitch = 1.0 + 0*0.3 - 0.9*0.2 = 0.82
    # tempo = 1.0 - 0*0.1 = 1.0
    # tone = "soft"
    expected_modulated_params = {"pitch": 0.82, "tempo": 1.0, "tone": "soft"}

    # Expected IR params
    expected_ir_params = {"decay": 1.2, "wet": 0.5}

    # Expected VPS output substrings
    expected_vps_output_substrings = [
        "simulated_audio_for_I_am..._so",
        f"_p{expected_modulated_params['pitch']}",
        f"_t{expected_modulated_params['tempo']}",
        f"_tone{expected_modulated_params['tone']}",
        f"_decay{expected_ir_params['decay']}",
        f"_wet{expected_ir_params['wet']}",
        f"_pause_s{pause_info[0]['start']}_d{pause_info[0]['duration']}"
    ]

    # Expected stereo depth output
    # pan = 0.3 * 0.0 - 0.2 * 0.0 = 0.0
    # depth = 1.0 - 0.9 * 0.5 = 0.55
    expected_sde_pan = 0.0
    expected_sde_depth = 0.55
    expected_sde_output_substrings = [
        "_binaural",
        f"_pan{expected_sde_pan}",
        f"_depth{expected_sde_depth}"
    ]

    result = run_voice_morph_workflow(text_content, emotion_vector, scene_context, pause_info)

    assert isinstance(result, str)
    for sub in expected_vps_output_substrings:
        assert sub in result
    for sub in expected_sde_output_substrings:
        assert sub in result

def test_run_voice_morph_workflow_neutral_outdoor():
    text_content = "The wind blows gently."
    emotion_vector = {"neutral": 1.0}
    scene_context = {"scene_type": "outdoor"}
    
    # Expected modulated voice params
    expected_modulated_params = {"pitch": 1.0, "tempo": 1.0, "tone": "neutral"}

    # Expected IR params
    expected_ir_params = {"decay": 0.1, "wet": 0.05}

    # Expected VPS output substrings
    expected_vps_output_substrings = [
        "simulated_audio_for_The_wind_b",
        f"_p{expected_modulated_params['pitch']}",
        f"_t{expected_modulated_params['tempo']}",
        f"_tone{expected_modulated_params['tone']}",
        f"_decay{expected_ir_params['decay']}", # Now expects 0.1 for outdoor
        f"_wet{expected_ir_params['wet']}"      # Now expects 0.05 for outdoor
    ]

    # Expected stereo depth output
    # pan = 0.0
    # depth = 1.0
    expected_sde_pan = 0.0
    expected_sde_depth = 1.0
    expected_sde_output_substrings = [
        "_binaural",
        f"_pan{expected_sde_pan}",
        f"_depth{expected_sde_depth}"
    ]

    result = run_voice_morph_workflow(text_content, emotion_vector, scene_context)

    assert isinstance(result, str)
    for sub in expected_vps_output_substrings:
        assert sub in result
    for sub in expected_sde_output_substrings:
        assert sub in result
