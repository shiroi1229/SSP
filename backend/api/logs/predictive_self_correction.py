# path: backend/api/logs/predictive_self_correction.py
# version: R-v1.1

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json
import os
from typing import List, Optional
from modules.log_manager import log_manager

router = APIRouter(prefix="/logs")

PREDICTIVE_LOG_PATH = "logs/predictive_self_correction.json"

class PredictiveLogEntry(BaseModel):
    timestamp: str
    cpu: Optional[float] = None
    mem: Optional[float] = None
    latency: Optional[float] = None
    predicted_probability: float = Field(default=0.0, alias="pred_prob")
    action: str
    context_id: Optional[str] = None

@router.get("/predictive-self-correction", response_model=List[PredictiveLogEntry])
async def get_predictive_self_correction_logs():
    """
    Retrieves all entries from the predictive self-correction log.
    """
    if not os.path.exists(PREDICTIVE_LOG_PATH):
        log_manager.info(f"Predictive self-correction log file not found at {PREDICTIVE_LOG_PATH}")
        return []

    try:
        with open(PREDICTIVE_LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        normalized = []
        for entry in logs:
            if not isinstance(entry, dict):
                continue
            # accept either pred_prob or predicted_probability
            if "predicted_probability" not in entry and "pred_prob" in entry:
                entry["predicted_probability"] = entry.get("pred_prob", 0.0)
            normalized.append(PredictiveLogEntry(**entry).model_dump(by_alias=False))
        return normalized
    except json.JSONDecodeError as e:
        log_manager.error(f"Error decoding JSON from {PREDICTIVE_LOG_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error reading predictive self-correction logs.")
    except Exception as e:
        log_manager.error(f"An unexpected error occurred while reading {PREDICTIVE_LOG_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
