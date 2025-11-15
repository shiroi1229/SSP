# path: modules/persona_manager.py
# version: v2.2

import datetime
import statistics
from orchestrator.context_manager import ContextManager
from modules.log_manager import log_manager

# Global in-memory store for the detailed emotion state
_current_detailed_emotion_state = {
    "joy": 0.5,
    "anger": 0.1,
    "sadness": 0.2,
    "happiness": 0.7,
    "fear": 0.05,
    "calm": 0.8,
}

def set_detailed_emotion_state(new_state: dict):
    """Updates the global detailed emotion state."""
    global _current_detailed_emotion_state
    _current_detailed_emotion_state = {**_current_detailed_emotion_state, **new_state}
    log_manager.info(f"[PersonaManager] Detailed emotion state updated: {_current_detailed_emotion_state}")

class PersonaManager:
    """Manages the AI's persona by observing the context and updating its state."""

    _has_logged_init = False

    def __init__(self):
        if not PersonaManager._has_logged_init:
            log_manager.info("[PersonaManager] Initialized.")
            PersonaManager._has_logged_init = True

    def _calculate_current_state(self, context_manager: ContextManager) -> dict:
        """Calculates the current harmony, focus, and emotion from the context."""
        optimization_log = context_manager.get("long_term.optimization_log") or []
        
        # Calculate harmony from recent evaluation scores
        evaluator_logs = [log for log in optimization_log if log.get("module") == "evaluator"]
        recent_scores = [log.get("evaluation_result", {}).get("rating", 0.5) for log in evaluator_logs[-10:]]
        harmony = statistics.mean(recent_scores) if recent_scores else 0.5

        # Placeholder logic for focus
        focus = 0.78
        
        # Use the globally managed detailed emotion state
        detailed_emotion_state = _current_detailed_emotion_state
        
        # Also keep a simplified emotion string for backward compatibility if needed
        emotion_string = "Calm"
        if harmony < 0.4:
            emotion_string = "Anxious"
        elif harmony > 0.8:
            emotion_string = "Pleased"

        return {
            "emotion": emotion_string, # Simplified string emotion
            "detailed_emotion_state": detailed_emotion_state, # New detailed emotion state
            "harmony": round(harmony, 2),
            "focus": focus
        }

    def _evolve_long_term_profile(self, context_manager: ContextManager):
        """Evolves the long-term persona profile based on performance trends."""
        # This is a simplified adaptation of the logic from persona_evolver.py
        optimization_log = context_manager.get("long_term.optimization_log") or []
        
        recent_scores = [log.get("evaluation_result", {}).get("rating", 0.5) for log in optimization_log[-20:] if log.get("module") == "evaluator"]
        performance_trend = statistics.mean(recent_scores) if recent_scores else 0.5

        def infer_trait(base_score, bias=0.0):
            base = 0.5 + (base_score - 0.5) * 0.2 + bias
            return max(0.0, min(1.0, round(base, 2)))

        new_traits = {
            "assertiveness": infer_trait(performance_trend),
            "empathy": infer_trait(1.0 - performance_trend), # Inverse relationship
            "curiosity": infer_trait(performance_trend, bias=0.1),
            "stability": infer_trait(1.0 - abs(performance_trend - 0.5)),
            "creativity": infer_trait(performance_trend)
        }

        profile = {
            "timestamp": datetime.datetime.now().isoformat(),
            "traits": new_traits
        }
        context_manager.set("long_term.persona_profile", profile, reason="Long-term persona profile evolved")
        log_manager.info(f"[PersonaManager] Long-term persona profile evolved: {new_traits}")

    def update_persona(self, context_manager: ContextManager):
        """Main method to update both short-term state and long-term profile."""
        log_manager.info("[PersonaManager] Running persona update cycle...")
        
        # Update short-term state
        persona_state = self._calculate_current_state(context_manager)
        context_manager.set("short_term.persona_state", persona_state, reason="Short-term persona state updated")
        log_manager.info(f"[PersonaManager] Short-term persona state updated: {persona_state}")

        # Evolve long-term profile
        self._evolve_long_term_profile(context_manager)

        log_manager.info("[PersonaManager] Persona update cycle complete.")

# Standalone function to get current persona state for external use (e.g., dashboard)
async def get_current_persona_state():
    # This is a simplified approach. In a more robust system, ContextManager
    # would be passed or retrieved from a global/singleton instance.
    # For now, we'll create a dummy ContextManager to allow _calculate_current_state to run.
    class DummyContextManager:
        def get(self, key):
            # Simulate fetching optimization_log for harmony calculation
            if key == "long_term.optimization_log":
                # Return some dummy data or read from a mock log file
                return [{"module": "evaluator", "evaluation_result": {"rating": 0.7}},
                        {"module": "evaluator", "evaluation_result": {"rating": 0.8}}]
            return None
        def set(self, key, value, reason):
            pass # Dummy set

    persona_manager = PersonaManager()
    dummy_context_manager = DummyContextManager()
    state = persona_manager._calculate_current_state(dummy_context_manager)
    # Add harmony_score alias for consistency with dashboard_ws.py
    state["harmony_score"] = state["harmony"]
    
    # Ensure the detailed_emotion_state is always present and up-to-date
    state["emotion_state"] = _current_detailed_emotion_state
    return state
