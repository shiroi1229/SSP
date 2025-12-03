# path: orchestrator/workflow.py
# version: v0.3
import os
import sys
import numpy as np
import hashlib
import json
from backend.dev_recorder import record_action
from modules.log_manager import LogManager
from orchestrator.context_manager import ContextManager
from orchestrator.query_processor import QueryProcessor
from modules.rag_engine import RAGEngine
from modules.generator import generate_response
from modules.evaluator import evaluate_output
from modules.memory_store import MemoryStore
from modules.motion_translator import emotion_to_motion
from modules.adaptive_physics import update_physics
from modules.smooth_transition_generator import generate_smooth_motion_transition
from modules.auto_pose_correction import auto_pose_correction
from modules.emotion_camera_sync_engine import camera_by_emotion
from modules.scene_layout_optimizer import optimize_scene_layout
from modules.adaptive_color_grader import adaptive_color_grade
from modules.render_cache_controller import get_cached_render, store_render_cache, clear_render_cache
from modules.emotion_modulation_network import modulate_voice_params
from modules.scene_acoustic_learner import generate_ir
from modules.voice_performance_synthesizer import synthesize_performance
from modules.stereo_depth_enhancer import stereo_depth

log_manager = LogManager()

def get_config(key, default=None):
    return os.getenv(key, default)

def _run_rag_engine(context_manager: ContextManager):
    user_input = context_manager.get("short_term.user_input")
    log_manager.info("[Workflow] --- RAG Engine: Start ---")
    try:
        rag_engine = RAGEngine()
        user_scope = context_manager.get("short_term.user.visibility", "public")
        processor = QueryProcessor(rag_engine, user_scope=user_scope)
        context = processor.build_context(user_input)
        context_manager.set("short_term.context", context)
        record_action("RAG", "get_context", {"user_input": user_input, "context": context})
    except Exception as e:
        log_manager.error(f"[Workflow] RAG Engine Error: {e}", exc_info=True)
        context_manager.set("short_term.context", f"RAG Engine Error: {e}")
    log_manager.info("[Workflow] --- RAG Engine: End ---")

def _run_generator(context_manager: ContextManager):
    user_input = context_manager.get("short_term.user_input")
    context = context_manager.get("short_term.context")
    log_manager.info("[Workflow] --- Generator: Start ---")
    model = get_config("GEMINI_MODEL", "gemini-pro")
    
    answer_str = generate_response(model=model, context=context, prompt=user_input)
    context_manager.set("short_term.generator_response", answer_str)
    context_manager.set("short_term.generator_prompt", f"Context: {context}\nUser Input: {user_input}")
    record_action("Generator", "generate_response", {"user_input": user_input, "context": context, "answer": answer_str})
    log_manager.info("[Workflow] --- Generator: End ---")

def _run_parser_and_evaluator(context_manager: ContextManager):
    full_lm_response_str = context_manager.get("short_term.generator_response")
    context = context_manager.get("short_term.context")
    
    if full_lm_response_str.startswith("シロイ: "):
        full_lm_response_str = full_lm_response_str[len("シロイ: "):]

    try:
        lm_response_json = json.loads(full_lm_response_str)
        answer = lm_response_json.get("final_output", full_lm_response_str)
        if "workflow_trace" in lm_response_json:
            context_manager.set("short_term.workflow_trace", lm_response_json["workflow_trace"])
    except json.JSONDecodeError as e:
        log_manager.warning(f"[Workflow] Failed to parse LM Studio JSON response: {e}")
        answer = full_lm_response_str

    context_manager.set("short_term.final_output", answer)

    eval_output = evaluate_output(answer, context)
    context_manager.set("short_term.feedback", eval_output)

def run_workflow(user_input: str) -> dict:
    context_manager = ContextManager()
    context_manager.set("short_term.user_input", user_input)
    context_manager.set("short_term.timestamp", datetime.datetime.now().isoformat())

    _run_rag_engine(context_manager)
    _run_generator(context_manager)
    _run_parser_and_evaluator(context_manager)

    log_data = context_manager.get_subset("short_term")
    
    memory_store = MemoryStore()
    memory_store.save_record_to_db(log_data)
    record_action("MemoryStore", "save_record", {"log_data": log_data})

    log_filename = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    log_path = os.path.join("logs", log_filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    log_manager.info(f"[Workflow] Workflow data logged to {log_path}")

    record_action("Workflow", "session_complete", {
        "session": log_filename,
        "final_output": log_data.get("final_output"),
        "evaluation_score": log_data.get("feedback", {}).get("score")
    })

    return log_data

def run_live2d_motion_workflow(emotion_input: dict, current_live2d_params: dict, emotion_harmony: float, delta_time: float = 0.016) -> dict:
    """
    Orchestrates the Live2D motion control pipeline based on emotion signals.

    Args:
        emotion_input (dict): A dictionary representing the emotion state,
                               e.g., {"joy": 0.7, "anger": 0.1, "sadness": 0.0}.
        current_live2d_params (dict): The current Live2D parameters of the model.
        emotion_harmony (float): A value representing the current emotional harmony (e.g., 0.0 to 1.0).
        delta_time (float): Time elapsed since the last update, for physics calculations.

    Returns:
        dict: A dictionary containing the final Live2D parameters after processing.
    """
    log_manager.info("[Workflow] --- Live2D Motion Workflow: Start ---")
    
    # 1. Emotion-to-Motion Translation
    target_motion_params = emotion_to_motion(emotion_input)
    log_manager.info(f"[Workflow] Emotion translated to target motion: {target_motion_params}")

    # 2. Smooth Transition Generation
    # Assuming current_live2d_params contains the actual current state of the Live2D model
    # and target_motion_params are the desired parameters from emotion_to_motion.
    # We'll use a fixed speed for now.
    transitioned_params = generate_smooth_motion_transition(current_live2d_params, target_motion_params, speed=0.3)
    log_manager.info(f"[Workflow] Motion transitioned smoothly: {transitioned_params}")

    # 3. Adaptive Physics Core
    # This module would typically update physics simulation parameters, not directly motion params.
    # For this placeholder, we'll assume it returns updated physics-related parameters
    # that might influence the final motion.
    updated_physics_params = update_physics(current_live2d_params, emotion_harmony, delta_time)
    log_manager.info(f"[Workflow] Physics updated: {updated_physics_params}")

    # For now, let's assume the physics updates are integrated into the transitioned_params
    # or are separate parameters. For simplicity, we'll just pass transitioned_params
    # to auto_pose_correction. In a real scenario, physics would apply to the model
    # and then pose correction might happen.
    
    # 4. Auto Pose Correction
    # We need a 'confidence' score here. For now, let's use a dummy value or derive it
    # from emotion_harmony (e.g., higher harmony -> higher confidence in current pose).
    # Let's assume a fixed confidence for now.
    confidence_score = 0.8 # This would ideally come from an AI model evaluating pose naturalness
    final_live2d_params = auto_pose_correction(transitioned_params, target_motion_params, confidence=confidence_score)
    log_manager.info(f"[Workflow] Pose corrected: {final_live2d_params}")

    log_manager.info("[Workflow] --- Live2D Motion Workflow: End ---")
    return final_live2d_params

def run_visual_composer_workflow(
    script_json: dict,
    emotion_vector: dict,
    audio_waveform: list,
    lighting_info: dict,
    current_frame: np.ndarray # Assuming a NumPy array for image frame
) -> dict:
    """
    Orchestrates the Visual Composer Engine Pro workflow to generate scene composition data.

    Args:
        script_json (dict): Script data in JSON format.
        emotion_vector (dict): A dictionary representing the emotion state.
        audio_waveform (list): Audio waveform data (e.g., peak detections).
        lighting_info (dict): Information about the scene's lighting.
        current_frame (np.ndarray): The current video frame as a NumPy array.

    Returns:
        dict: A dictionary containing the final scene composition, including camera settings
              and color-graded frame (or reference).
    """
    log_manager.info("[Workflow] --- Visual Composer Workflow: Start ---")

    scene_composition = {}

    # 1. Emotion-Camera Sync Engine
    camera_preset = camera_by_emotion(emotion_vector)
    scene_composition["camera_preset"] = camera_preset
    log_manager.info(f"[Workflow] Camera preset determined: {camera_preset}")

    # 2. Scene Layout Optimizer
    optimized_layout = optimize_scene_layout(script_json, audio_waveform, emotion_vector)
    scene_composition["optimized_layout"] = optimized_layout
    log_manager.info(f"[Workflow] Scene layout optimized: {optimized_layout}")

    # 3. Adaptive Color Grader
    color_graded_frame = adaptive_color_grade(current_frame, emotion_vector, lighting_info)
    # In a real scenario, this would be saved to a temporary file or passed as a reference
    scene_composition["color_graded_frame_ref"] = "reference_to_color_graded_frame" # Placeholder
    log_manager.info("[Workflow] Frame color graded.")

    # 4. Render Cache Controller (Integration example)
    # Generate a cache key based on relevant parameters
    # For simplicity, emotion_hash and lighting_profile are derived here.
    emotion_hash = hashlib.md5(json.dumps(emotion_vector, sort_keys=True).encode('utf-8')).hexdigest()
    lighting_profile_str = json.dumps(lighting_info, sort_keys=True) if lighting_info else ""
    lighting_profile_hash = hashlib.md5(lighting_profile_str.encode('utf-8')).hexdigest()
    
    scene_id = script_json.get("title", "default_scene") # Use scene title as ID
    cache_key_params = (scene_id, emotion_hash, lighting_profile_hash)

    cached_result = get_cached_render(*cache_key_params)
    if cached_result:
        scene_composition["render_source"] = "cache"
        scene_composition["final_render_ref"] = cached_result
        log_manager.info(f"[Workflow] Render result retrieved from cache: {cached_result}")
    else:
        # Simulate rendering and store in cache
        simulated_render_output = f"path/to/rendered/{scene_id}_{emotion_hash}.mp4"
        store_render_cache(*cache_key_params, simulated_render_output)
        scene_composition["render_source"] = "new_render"
        scene_composition["final_render_ref"] = simulated_render_output
        log_manager.info(f"[Workflow] Render result generated and stored: {simulated_render_output}")

    log_manager.info("[Workflow] --- Visual Composer Workflow: End ---")
    return scene_composition

def run_voice_morph_workflow(
    text_content: str,
    emotion_vector: dict,
    scene_context: dict,
    pause_info: list = None
) -> str:
    """
    Orchestrates the Voice Morph Engine Advanced workflow to generate expressive and spatially
    enhanced audio.

    Args:
        text_content (str): The text to be spoken.
        emotion_vector (dict): A dictionary representing the emotion state.
        scene_context (dict): Information about the current scene, including acoustic properties.
        pause_info (list, optional): List of dictionaries specifying pauses. Defaults to None.

    Returns:
        str: The final processed audio data (simulated).
    """
    log_manager.info("[Workflow] --- Voice Morph Workflow: Start ---")

    # 1. Emotion Modulation Network
    modulated_voice_params = modulate_voice_params(emotion_vector)
    log_manager.info(f"[Workflow] Modulated voice parameters: {modulated_voice_params}")

    # 2. Scene Acoustic Learner
    ir_params = generate_ir(scene_context.get("scene_type", "studio"))
    log_manager.info(f"[Workflow] Generated IR parameters: {ir_params}")

    # 3. Voice Performance Synthesizer
    # This step would typically use TTS Manager and integrate modulated_voice_params and ir_params
    # For now, we'll pass them conceptually to synthesize_performance
    simulated_audio_from_vps = synthesize_performance(
        text_content,
        emotion_vector, # Pass emotion for internal logic of VPS
        scene_context,  # Pass scene context for internal logic of VPS
        pause_info      # Pass pause info
    )
    log_manager.info(f"[Workflow] Simulated audio from VPS: {simulated_audio_from_vps}")

    # 4. Stereo Depth Enhancer
    final_processed_audio = stereo_depth(simulated_audio_from_vps, emotion_vector)
    log_manager.info(f"[Workflow] Final processed audio with stereo depth: {final_processed_audio}")

    log_manager.info("[Workflow] --- Voice Morph Workflow: End ---")
    return final_processed_audio