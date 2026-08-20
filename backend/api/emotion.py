from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from backend.db.connection import get_db
from modules.persona_manager import set_detailed_emotion_state # Import the setter function

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

class EmotionStateUpdate(BaseModel):
    joy: float
    anger: float
    sadness: float
    happiness: float
    fear: float
    calm: float

@router.post("/emotion")
async def update_emotion_state(emotion_state: EmotionStateUpdate, db: Session = Depends(get_db)):
    """
    Receives updated emotion state from the frontend and processes it.
    This will now update the AI's internal emotion model via persona_manager.
    """
    logger.info(f"Received emotion state update: {emotion_state.model_dump_json()}")
    
    # Update the global detailed emotion state in persona_manager
    set_detailed_emotion_state(emotion_state.model_dump())
    
    return {"message": "Emotion state received", "status": "success", "data": emotion_state}