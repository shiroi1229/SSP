# path: backend/api/osc.py
# version: v1
# API endpoint to send emotion data to VTube Studio via OSC.

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from modules.osc_bridge import OSCBridge

import logging # Add logging import

router = APIRouter(prefix="/api")
osc_bridge = OSCBridge()
logger = logging.getLogger(__name__) # Initialize logger

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
        logger.error("OSC client is not available for /osc/send. Check host/port.")
        raise HTTPException(status_code=500, detail="OSC client is not available. Check host/port.")
    
    logger.info(f"Attempting to send OSC emotion: {payload.emotion.dict()}")
    result = osc_bridge.send_emotion(payload.emotion.dict())
    logger.info(f"OSC send result: {result}")
    return result

class OSCSendEmotionRequest(BaseModel):
    emotion: str
    intensity: float

@router.post("/osc/send-emotion")
async def send_specific_osc_emotion(payload: OSCSendEmotionRequest):
    """
    Receives a specific emotion and intensity and forwards it to the OSC bridge.
    """
    if not osc_bridge.client:
        logger.error("OSC client is not available for /osc/send-emotion. Check host/port.")
        raise HTTPException(status_code=500, detail="OSC client is not available. Check host/port.")
    
    osc_data = {"emotion_tags": [payload.emotion], "intensity": payload.intensity}
    logger.info(f"Attempting to send specific OSC emotion: {osc_data}")
    result = osc_bridge.send_emotion(osc_data)
    logger.info(f"Specific OSC send result: {result}")
    return result
