import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.scene_acoustic_learner import generate_ir

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('modules.scene_acoustic_learner.logger', MagicMock()) as mock_sal_logger:
        yield

def test_generate_ir_studio():
    scene_type = "studio"
    expected_ir = {"decay": 0.2, "wet": 0.1}
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_hall():
    scene_type = "hall"
    expected_ir = {"decay": 1.2, "wet": 0.5}
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_metal_room():
    scene_type = "metal_room"
    expected_ir = {"decay": 0.8, "wet": 0.4}
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_outdoor():
    scene_type = "outdoor"
    expected_ir = {"decay": 0.1, "wet": 0.05}
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_cave():
    scene_type = "cave"
    expected_ir = {"decay": 2.5, "wet": 0.7}
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_unknown_scene_defaults_to_studio():
    scene_type = "unknown_forest"
    expected_ir = {"decay": 0.2, "wet": 0.1} # Should default to studio
    assert generate_ir(scene_type) == expected_ir

def test_generate_ir_empty_scene_defaults_to_studio():
    scene_type = ""
    expected_ir = {"decay": 0.2, "wet": 0.1} # Should default to studio
    assert generate_ir(scene_type) == expected_ir
