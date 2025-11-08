# path: backend/api/emotion.py
# version: v1
# Emotion Engine REST API
from fastapi import APIRouter, Body
from pydantic import BaseModel
from modules.emotion_engine import EmotionEngine
from typing import Dict

router = APIRouter(prefix="/api")
engine = EmotionEngine()

class EmotionRequest(BaseModel):
    text: str

@router.post("/emotion", response_model=Dict)
async def analyze_emotion_endpoint(payload: EmotionRequest):
    """
    Analyzes the emotion of a given text.
    """
    text = payload.text
    result = engine.analyze(text)
    return {"input": text, "emotion": result}
