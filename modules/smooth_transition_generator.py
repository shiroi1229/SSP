import logging

logger = logging.getLogger(__name__)

def smooth_transition(current_value: float, target_value: float, speed: float = 0.1) -> float:
    """
    Generates a smoothly transitioning value between current and target.

    Args:
        current_value (float): The current value.
        target_value (float): The desired target value.
        speed (float): The interpolation speed (0.0 to 1.0). Higher speed means faster transition.

    Returns:
        float: The interpolated value.
    """
    # This is a simple linear interpolation (lerp). More advanced easing functions
    # (e.g., easeInOutCubic as mentioned in the roadmap) could be implemented here.
    interpolated_value = current_value + (target_value - current_value) * speed
    return interpolated_value

def generate_smooth_motion_transition(
    current_params: dict, 
    target_params: dict, 
    speed: float = 0.1
) -> dict:
    """
    Generates smoothly transitioning motion parameters from current to target.

    Args:
        current_params (dict): Dictionary of current Live2D motion parameters.
        target_params (dict): Dictionary of target Live2D motion parameters.
        speed (float): The interpolation speed for each parameter.

    Returns:
        dict: Dictionary of interpolated Live2D motion parameters.
    """
    logger.info(f"Generating smooth transition from {current_params} to {target_params} with speed {speed}")
    
    transitioned_params = {}
    for param_name, current_val in current_params.items():
        if param_name in target_params:
            target_val = target_params[param_name]
            transitioned_params[param_name] = smooth_transition(current_val, target_val, speed)
        else:
            transitioned_params[param_name] = current_val # Keep current if no target
            
    logger.info(f"Transitioned parameters: {transitioned_params}")
    return transitioned_params

if __name__ == "__main__":
    # Example Usage
    current = {"eyeOpen": 0.5, "mouthForm": 0.2, "browY": 0.0}
    target = {"eyeOpen": 1.0, "mouthForm": 0.8, "browY": 0.5}

    # Simulate a few frames of transition
    print(f"Initial: {current}")
    for i in range(5):
        current = generate_smooth_motion_transition(current, target, speed=0.2)
        print(f"Frame {i+1}: {current}")

    current_single = 0.1
    target_single = 0.9
    print(f"\nSingle value transition from {current_single} to {target_single}:")
    for i in range(5):
        current_single = smooth_transition(current_single, target_single, speed=0.3)
        print(f"Step {i+1}: {current_single}")
