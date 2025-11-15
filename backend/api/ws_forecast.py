# path: backend/api/ws_forecast.py
# version: R-v1.1
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from modules.log_manager import log_manager
import asyncio

router = APIRouter()

@router.websocket("/ws/forecast")
async def forecast_stream(ws: WebSocket):
    await ws.accept()
    log_manager.info("[WebSocket] Forecast client connected.")
    
    # InsightMonitor's constructor needs arguments. Since forecast_anomaly
    # is self-contained for now, we can pass dummy/default instances.
    dummy_context = ContextManager()
    dummy_policy = RecoveryPolicyManager()
    monitor = InsightMonitor(dummy_context, dummy_policy)
    
    try:
        while True:
            result = monitor.forecast_anomaly()
            await ws.send_json(result)
            await asyncio.sleep(10)  # 10秒ごとに更新
    except WebSocketDisconnect:
        log_manager.info("[WebSocket] Forecast client disconnected.")
    except Exception as e:
        log_manager.error(f"[WebSocket] Error in forecast stream: {e}", exc_info=True)
        try:
            await ws.send_json({"error": str(e)})
        except Exception as send_e:
            log_manager.error(f"[WebSocket] Failed to send error to client: {send_e}", exc_info=True)
    finally:
        # The connection might already be closed, so this might fail
        try:
            await ws.close()
        except RuntimeError:
            pass # Connection already closed
        log_manager.info("[WebSocket] Forecast stream closed.")
