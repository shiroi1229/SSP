# path: backend/api/status.py
# version: v1
import time
import requests
import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.connection import get_db

router = APIRouter(prefix="/api")

# --- Helper function to load config ---
def get_llm_url():
    """Loads the LLM URL from config file or environment variables."""
    config_path = "./config/model_params.json"
    default_url = "http://127.0.0.1:1234" # Default from llm.py
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("llm_url", default_url)
        except (json.JSONDecodeError, IOError):
            pass # Fallback to env var or default
            
    return os.getenv("LOCAL_LLM_API_URL", default_url)

# --- Status Check Functions ---
async def check_database_status(db: Session):
    """Checks the status of the PostgreSQL database."""
    start_time = time.time()
    try:
        db.execute("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        return {"name": "Database (PostgreSQL)", "status": "online", "response_time_ms": round(response_time)}
    except Exception:
        return {"name": "Database (PostgreSQL)", "status": "offline"}

async def check_qdrant_status():
    """Checks the status of the Qdrant vector database."""
    url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    start_time = time.time()
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        response_time = (time.time() - start_time) * 1000
        return {"name": "Vector DB (Qdrant)", "status": "online", "response_time_ms": round(response_time)}
    except requests.RequestException:
        return {"name": "Vector DB (Qdrant)", "status": "offline"}

async def check_llm_status():
    """Checks the status of the LLM service (e.g., LM Studio)."""
    url = get_llm_url()
    # The full endpoint is /v1/chat/completions, but we check the base URL or a models endpoint
    # as a general health check. LM Studio's base URL doesn't return anything, so let's check models.
    check_url = f"{url.replace('/v1', '')}/v1/models"
    start_time = time.time()
    try:
        response = requests.get(check_url, timeout=10)
        response.raise_for_status()
        response_time = (time.time() - start_time) * 1000
        return {"name": "LLM (LM Studio)", "status": "online", "response_time_ms": round(response_time)}
    except requests.RequestException:
        return {"name": "LLM (LM Studio)", "status": "offline"}

# --- Main Endpoint ---
@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    """
    Checks and returns the status of all major system components and external services.
    """
    # For internal modules, if the API is up, they are considered 'online'.
    # We can add more sophisticated checks later if needed.
    internal_modules = [
        {"name": "orchestrator", "status": "online", "last_updated": time.time()},
        {"name": "generator", "status": "online", "last_updated": time.time()},
        {"name": "evaluator", "status": "online", "last_updated": time.time()},
    ]
    
    # Check external services concurrently (though this is a simple example)
    db_status = await check_database_status(db)
    qdrant_status = await check_qdrant_status()
    llm_status = await check_llm_status()
    
    all_statuses = internal_modules + [db_status, qdrant_status, llm_status]
    
    # Format for frontend
    for module in all_statuses:
        if "last_updated" in module:
            module["last_updated"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(module["last_updated"]))

    return {"modules": all_statuses}
