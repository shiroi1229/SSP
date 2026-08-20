from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

# Assuming orchestrator is in the Python path
from orchestrator.main import run_context_evolution_cycle

router = APIRouter()

class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    ai_response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    logging.info(f"Received chat message: {request.user_input}")
    try:
        # This is a fire-and-forget call now
        run_context_evolution_cycle(request.user_input)
        ai_response = "Processing your request."
        return ChatResponse(ai_response=ai_response)
    except Exception as e:
        logging.error(f"Error handling chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
