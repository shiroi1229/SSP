from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

# Assuming orchestrator is in the Python path
from orchestrator.main import handle_chat_message

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    ai_response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    logging.info(f"Received chat message: {request.user_input}")
    try:
        ai_response = await handle_chat_message(request.user_input)
        return ChatResponse(ai_response=ai_response)
    except Exception as e:
        logging.error(f"Error handling chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")