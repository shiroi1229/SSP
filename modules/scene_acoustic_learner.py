import logging

logger = logging.getLogger(__name__)

def generate_ir(scene_type: str) -> dict:
    """
    Generates Impulse Response (IR) parameters (decay, wet) based on the scene type.
    This simulates the learning and generation of acoustic properties for a given environment.

    Args:
        scene_type (str): A string representing the type of scene (e.g., "studio", "hall", "metal_room", "outdoor").

    Returns:
        dict: A dictionary of IR parameters, e.g., {"decay": 0.2, "wet": 0.1}.
    """
    logger.info(f"Generating Impulse Response for scene type: {scene_type}")

    presets = {
        "studio": {"decay": 0.2, "wet": 0.1},
        "hall": {"decay": 1.2, "wet": 0.5},
        "metal_room": {"decay": 0.8, "wet": 0.4},
        "outdoor": {"decay": 0.1, "wet": 0.05}, # Very short decay, low wet for open spaces
        "cave": {"decay": 2.5, "wet": 0.7}, # Long decay, high wet for echoey spaces
        # Add more scene types and their corresponding IR parameters
    }

    # Get preset, default to "studio" if scene_type is unknown
    ir_params = presets.get(scene_type, presets["studio"])
    
    logger.info(f"Generated IR parameters: {ir_params}")
    return ir_params

if __name__ == "__main__":
    # Example Usage
    ir_studio = generate_ir("studio")
    print(f"Studio IR: {ir_studio}")

    ir_hall = generate_ir("hall")
    print(f"Hall IR: {ir_hall}")

    ir_metal_room = generate_ir("metal_room")
    print(f"Metal Room IR: {ir_metal_room}")

    ir_outdoor = generate_ir("outdoor")
    print(f"Outdoor IR: {ir_outdoor}")

    ir_unknown = generate_ir("unknown_scene")
    print(f"Unknown Scene IR (defaults to studio): {ir_unknown}")
