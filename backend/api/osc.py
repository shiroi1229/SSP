# path: backend/api/osc.py
# version: v1
# API endpoint to send emotion data to VTube Studio via OSC.

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from modules.osc_bridge import OSCBridge

router = APIRouter(prefix="/api")
osc_bridge = OSCBridge()

class EmotionPayload(BaseModel):
    emotion_tags: List[str] = Field(default_factory=lambda: ["Neutral"])
    intensity: float = 0.5

class OSCRequest(BaseModel):
    emotion: EmotionPayload

@router.post("/osc/send")
async def send_osc_emotion(payload: OSCRequest):
    """
    Receives emotion data and forwards it to the OSC bridge to control VTube Studio.
    """
    if not osc_bridge.client:
        raise HTTPException(status_code=500, detail="OSC client is not available. Check host/port.")
    
    result = osc_bridge.send_emotion(payload.emotion.dict())
    return result
