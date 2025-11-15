# path: backend/api/system_forecast.py
# version: R-v1.1

from fastapi import APIRouter
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager

router = APIRouter()

@router.get("/system/forecast")
async def forecast_system_health():
    """
    Returns predicted anomaly probability and preventive action result.
    """
    # The InsightMonitor constructor requires arguments that are not used by 
    # the forecast_anomaly method. We can pass dummy arguments.
    # This is a workaround for the current design.
    dummy_context_manager = ContextManager(history_path="logs/context_history.json", context_filepath="data/test_context.json")
    dummy_policy_manager = RecoveryPolicyManager()
    monitor = InsightMonitor(dummy_context_manager, dummy_policy_manager)
    
    result = monitor.forecast_anomaly()
    return {"status": "ok", "forecast": result}
