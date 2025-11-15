# path: backend/api/system_health.py
# version: R-v1.0

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import psutil
import time
import datetime
import os
from modules.log_manager import log_manager
from orchestrator.context_manager import ContextManager # Import ContextManager

router = APIRouter(prefix="/system")

# Global instance of ContextManager (assuming it's a singleton or managed globally)
# In a more complex application, this might be managed via FastAPI's dependency injection
# or a dedicated application state. For now, we'll assume a simple global access.
# This will be properly initialized in backend/main.py
context_manager_instance: ContextManager = None

def get_context_manager() -> ContextManager:
    if context_manager_instance is None:
        # This should ideally not happen if backend/main.py initializes it correctly
        log_manager.error("ContextManager instance not initialized in system_health.py!")
        raise HTTPException(status_code=500, detail="ContextManager not initialized.")
    return context_manager_instance

class SystemHealth(BaseModel):
    cpu_percent: float
    memory_percent: float
    uptime_seconds: float
    uptime_human: str
    process_count: int
    disk_usage_percent: float
    boot_time: str

class AnomalyForecast(BaseModel):
    predicted_anomaly_probability: float
    timestamp: str

@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """
    Retrieves current system health metrics.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1) # Non-blocking
        memory_percent = psutil.virtual_memory().percent
        
        boot_timestamp = psutil.boot_time()
        uptime_seconds = time.time() - boot_timestamp
        uptime_human = str(datetime.timedelta(seconds=int(uptime_seconds)))

        process_count = len(psutil.pids())
        
        # Get disk usage for the current drive where the script is running
        current_drive = os.path.splitdrive(os.getcwd())[0]
        disk_usage = psutil.disk_usage(current_drive)
        disk_usage_percent = disk_usage.percent

        log_manager.debug(f"System health metrics collected: CPU={cpu_percent}%, Mem={memory_percent}%")

        return SystemHealth(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            uptime_seconds=uptime_seconds,
            uptime_human=uptime_human,
            process_count=process_count,
            disk_usage_percent=disk_usage_percent,
            boot_time=datetime.datetime.fromtimestamp(boot_timestamp).isoformat()
        )
    except Exception as e:
        log_manager.error(f"Error collecting system health metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system health: {e}")

@router.get("/forecast", response_model=AnomalyForecast)
async def get_anomaly_forecast(context_manager: ContextManager = Depends(get_context_manager)):
    """
    Retrieves the predicted anomaly probability from the Predictive Analyzer.
    """
    predicted_prob = context_manager.get("mid_term.predicted_anomaly_probability", default=0.0)
    current_timestamp = datetime.datetime.now().isoformat()
    log_manager.debug(f"Anomaly forecast requested: Predicted Probability={predicted_prob}")
    return AnomalyForecast(predicted_anomaly_probability=predicted_prob, timestamp=current_timestamp)
