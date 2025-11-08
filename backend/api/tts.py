# path: backend/api/tts.py
# version: v1
# Text-to-Speech (TTS) API endpoint

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from modules.tts_manager import TTSManager
from modules.emotion_engine import EmotionEngine

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

    # 1. Analyze emotion from the text
    emotion_data = emotion_engine.analyze(text)
    if "error" in emotion_data:
        # If emotion analysis fails, proceed with Neutral emotion
        emotion_data = {"emotion_tags": ["Neutral"], "intensity": 0.5}

    # 2. Synthesize speech with the analyzed emotion
    audio_path = tts_manager.synthesize(text, emotion_data, speaker_id)
    
    if "Error" in audio_path:
        raise HTTPException(status_code=500, detail=audio_path)

    return {
        "text": text,
        "emotion": emotion_data,
        "speaker_id": speaker_id,
        "audio_path": audio_path,
    }
