from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any

# Assuming orchestrator is in the Python path
from orchestrator.main import get_current_context

router = APIRouter(prefix="/api")

class ContextResponse(BaseModel):
    short_term: Dict[str, Any]
    mid_term: Dict[str, Any]
    long_term: Dict[str, Any]

@router.get("/context", response_model=ContextResponse)
async def context_endpoint():
    logging.info("Received request for current context.")
    try:
        current_context = await get_current_context()
        return ContextResponse(**current_context)
    except Exception as e:
        logging.error(f"Error retrieving context: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
