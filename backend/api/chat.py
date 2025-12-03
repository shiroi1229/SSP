from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging

# Assuming orchestrator is in the Python path
from orchestrator.main import run_context_evolution_cycle

router = APIRouter()

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    ai_response: str


def _run_context_cycle(user_input: str) -> None:
    """Execute the context evolution cycle with error handling."""
    try:
        run_context_evolution_cycle(user_input)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error running context evolution cycle", exc_info=exc)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    logger.info("Received chat message: %s", request.user_input)
    try:
        background_tasks.add_task(_run_context_cycle, request.user_input)
        return ChatResponse(ai_response="Processing your request.")
    except Exception as exc:
        logger.exception("Error scheduling chat message", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal Server Error")
