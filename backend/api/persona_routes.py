# path: backend/api/persona_routes.py
# version: v1.3
"""
Persona Dashboard（UI-v1.3）のバックエンドAPI群。
AI人格の状態取得・更新、メモリスナップ取得、文脈同期状態を提供する。
Context Evolution Framework (v2.4) および Memory Store (core) と連携。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json, os

router = APIRouter(prefix="/persona", tags=["Persona"])

# ---- データモデル ---- #
class EmotionState(BaseModel):
    joy: float
    sad: float
    neutral: float

class PersonaState(BaseModel):
    persona_id: str
    emotion_state: EmotionState
    tone: str
    logic_ratio: float
    creativity_ratio: float
    memory_usage: float
    context_sync_rate: float
    last_update: str

# ---- 疑似DBパス ---- #
PERSONA_STATE_FILE = "data/persona_state.json"
MEMORY_SNAPSHOT_FILE = "data/memory_log.json"

# ---- API定義 ---- #

@router.get("/state", response_model=PersonaState)
async def get_persona_state():
    """現在の人格状態を取得"""
    if not os.path.exists(PERSONA_STATE_FILE):
        raise HTTPException(status_code=404, detail="Persona state file not found")
    with open(PERSONA_STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@router.post("/update_state")
async def update_persona_state(state: PersonaState):
    """人格パラメータを更新・保存"""
    state.last_update = datetime.utcnow().isoformat()
    with open(PERSONA_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state.dict(), f, ensure_ascii=False, indent=2)
    return {"status": "ok", "updated_at": state.last_update}

@router.get("/memory_snapshot")
async def get_memory_snapshot():
    """記憶スナップショット一覧を取得"""
    if not os.path.exists(MEMORY_SNAPSHOT_FILE):
        # Create an empty list if the file doesn't exist
        return []
    with open(MEMORY_SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return [] # Return empty list if file is empty or malformed
    # 最新10件を返す
    return data[-10:] if isinstance(data, list) else [data]

@router.get("/context_sync")
async def get_context_sync_status():
    """Context Evolution Frameworkの同期状態を取得"""
    # 将来はv2.4 Context Monitor から動的取得
    dummy_sync = {
        "context_sync_rate": 0.94,
        "latency_ms": 122,
        "active_contexts": 12,
        "last_update": datetime.utcnow().isoformat()
    }
    return dummy_sync
