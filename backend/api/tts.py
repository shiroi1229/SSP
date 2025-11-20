# path: backend/api/tts.py
# version: v1
# Text-to-Speech (TTS) API endpoint

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from modules.tts_manager import TTSManager
from modules.emotion_engine import EmotionEngine
import time

router = APIRouter(prefix="/api")
tts_manager = TTSManager()
emotion_engine = EmotionEngine()

class TTSRequest(BaseModel):
    text: str
    speaker_id: int = 1

@router.post("/tts")
async def generate_tts_endpoint(payload: TTSRequest):
    """
    Analyzes emotion from text and generates speech.
    """
    text = payload.text
    speaker_id = payload.speaker_id

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    start = time.perf_counter()
    emotion_data = emotion_engine.analyze(text)
    if "error" in emotion_data:
        emotion_data = {"emotion_tags": ["Neutral"], "intensity": 0.5}

    audio_path, fallback_used, error_code = tts_manager.synthesize(text, emotion_data, speaker_id)
    latency_ms = int((time.perf_counter() - start) * 1000)

    if fallback_used or not audio_path:
        detail = error_code or "Unknown TTS failure"
        raise HTTPException(status_code=503, detail=detail)

    return {
        "text": text,
        "emotion": emotion_data,
        "speaker_id": speaker_id,
        "audio_path": audio_path,
        "tts_latency_ms": latency_ms,
        "fallback_used": fallback_used,
        "error_code": error_code,
    }
