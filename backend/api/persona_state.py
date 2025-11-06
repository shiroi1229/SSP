# path: backend/api/persona_state.py
# version: v0.3

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Persona"])

@router.get("/persona/state")
def get_persona_state():
    persona_state = {
        "status": "ok",
        "persona": "Shiroi",
        "timestamp": datetime.utcnow().isoformat(),
        "emotion": {
            "valence": 0.45,   # 快／不快（−1〜1）
            "arousal": 0.32,   # 興奮度（0〜1）
            "label": "Calm Focus"
        },
        "harmony": 0.84,         # 内的調和
        "focus": 0.78,           # 集中度
        "cognitive_harmony": 84.0,  # UIが%表示する値
        "introspection_logs": [
            {"stage": "self_evaluation", "comment": "世界観整合性良好。文体の一貫性向上を提案。"},
            {"stage": "final_output", "comment": "人格安定モード。生成結果は安定。"}
        ]
    }
    return persona_state