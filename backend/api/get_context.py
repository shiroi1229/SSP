from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from typing import Dict, Any

from backend.container import AppContainer, get_context_manager
from orchestrator.context_manager import ContextManager

router = APIRouter(prefix="/api")

class ContextResponse(BaseModel):
    short_term: Dict[str, Any]
    mid_term: Dict[str, Any]
    long_term: Dict[str, Any]

@router.get("/context", response_model=ContextResponse)
def context_endpoint(context_manager: ContextManager = Depends(get_context_manager)):
    logging.info("Received request for current context.")
    try:
        # The get_all_layers method returns a dict with the layer names as keys
        current_context = context_manager.get_all_layers()
        return ContextResponse(**current_context)
    except Exception as e:
        logging.error(f"Error retrieving context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
