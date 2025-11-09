# path: backend/api/context.py
# version: v2.2
from fastapi import APIRouter

# from orchestrator.shared import context_manager # TODO: Implement shared context

router = APIRouter()

@router.get("/context/state")
async def get_context_state():
    """Provides a snapshot of the AI's current internal state for visualization."""
    
    # --- Mock Data --- 
    # This data will be replaced by actual calls to the ContextManager.
    persona_state = {
        "emotion": "Curious",
        "harmony": 0.75,
        "focus": 0.88
    }
    cognitive_harmony = {
        "score": 75,
        "emotion": "Curious"
    }
    introspection_logs = [
        "self_evaluation: New optimization cycle started.",
        "evaluator: Score calculated: 0.88",
        "persona_manager: Persona state updated."
    ]
    evaluation_score = 0.88
    generated_output = "これは、v2.2のマルチモジュール最適化サイクルで生成された回答のプレースホルダーです。"
    # --- End Mock Data ---

    # In the future, this will be replaced with:
    # persona_state = context_manager.get("short_term.persona_state")
    # evaluation_score = context_manager.get("mid_term.evaluation_score")
    # generated_output = context_manager.get("mid_term.generated_output")
    # ... and so on

    return {
        "personaState": persona_state,
        "cognitiveHarmony": cognitive_harmony, # This might be derived from personaState.harmony
        "introspectionLogs": introspection_logs,
        "evaluationScore": evaluation_score,
        "generatedOutput": generated_output,
    }
