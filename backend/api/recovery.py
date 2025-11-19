"""Recovery endpoints for manual control and resync."""

from fastapi import APIRouter, HTTPException

from modules.distributed_recovery_manager import manager as recovery_manager
from modules.state_resync import capture_state_snapshot
from modules.failure_logger import failure_logger

router = APIRouter(prefix="/recovery", tags=["Recovery"])


@router.post("/restart")
def restart_module(standby_name: str):
    try:
        result = recovery_manager.promote(standby_name)
        failure_logger.log_info("Manual restart", {"module": standby_name})
        return {"status": "ok", "module": standby_name, "result": result}
    except Exception as exc:
        failure_logger.log_failure(exc, context=f"restart {standby_name}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/state_resync")
def resync_state():
    snapshot = capture_state_snapshot()
    failure_logger.log_info("State resync", {"snapshot": snapshot.get("path")})
    return {"status": "resynced", "snapshot": snapshot}
