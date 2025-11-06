# path: modules/persona_manager.py
# version: v2.2

import datetime
import statistics
from orchestrator.context_manager import ContextManager
from modules.log_manager import log_manager

class PersonaManager:
    """Manages the AI's persona by observing the context and updating its state."""

    def __init__(self):
        log_manager.info("[PersonaManager] Initialized.")

    def _calculate_current_state(self, context_manager: ContextManager) -> dict:
        """Calculates the current harmony, focus, and emotion from the context."""
        optimization_log = context_manager.get("long_term.optimization_log") or []
        
        # Calculate harmony from recent evaluation scores
        evaluator_logs = [log for log in optimization_log if log.get("module") == "evaluator"]
        recent_scores = [log.get("evaluation_result", {}).get("rating", 0.5) for log in evaluator_logs[-10:]]
        harmony = statistics.mean(recent_scores) if recent_scores else 0.5

        # Placeholder logic for focus and emotion
        focus = 0.78
        emotion = "Calm"
        if harmony < 0.4:
            emotion = "Anxious"
        elif harmony > 0.8:
            emotion = "Pleased"

        return {
            "emotion": emotion,
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
