# path: orchestrator/predictive_scheduler.py
# version: R-v1.1
"""
Nightly Predictive Self-Correction Scheduler.
Runs InsightMonitor.forecast_anomaly() once per scheduled cycle.
"""

import asyncio
import time
import json
from datetime import datetime
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from modules.log_manager import log_manager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from modules.predictive_trainer import PredictiveTrainer

LOG_PATH = "logs/predictive_self_correction.json"

async def run_predictive_cycle():
    """
    Executes one predictive cycle: forecast, log, and potentially act.
    Also triggers model retraining on a schedule (e.g., weekly).
    """
    log_manager.info("[PredictiveScheduler] Starting forecast cycle...")
    # InsightMonitor's constructor needs arguments. Since forecast_anomaly
    # is self-contained for now, we can pass dummy/default instances.
    dummy_context = ContextManager()
    dummy_policy = RecoveryPolicyManager()
    monitor = InsightMonitor(dummy_context, dummy_policy)
    
    result = monitor.forecast_anomaly()
    timestamp = datetime.utcnow().isoformat()

    # The log format in the spec is slightly different from what forecast_anomaly returns.
    # The spec wants the log entry itself to be written to predictive_self_correction.json
    # but forecast_anomaly already writes a similar log.
    # For now, we will log the summary as requested by the spec to a *different* file
    # to avoid corrupting the JSON list structure of the other log.
    # Let's create a summary log.
    summary_log_path = "logs/predictive_scheduler_summary.jsonl"
    entry = {"timestamp": timestamp, "forecast": result}
    log_manager.info(f"[PredictiveScheduler] Forecast cycle result: {result}")

    try:
        with open(summary_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log_manager.error(f"[PredictiveScheduler] Failed to write summary log: {e}", exc_info=True)

    # After forecast run, retrain model periodically (e.g., once per week on Sunday)
    if datetime.utcnow().weekday() == 6:  # 6 corresponds to Sunday
        log_manager.info("[PredictiveScheduler] It's Sunday. Starting weekly model retraining cycle.")
        try:
            trainer = PredictiveTrainer()
            training_result = trainer.evaluate_and_replace()
            log_manager.info(f"[PredictiveScheduler] Weekly training cycle finished. Result: {training_result}")
        except Exception as e:
            log_manager.error(f"[PredictiveScheduler] An error occurred during the training cycle: {e}", exc_info=True)


async def start_predictive_scheduler(interval_seconds: int = None):
    """
    Schedules nightly predictive cycles.
    If interval_seconds is provided, it runs at that interval for testing.
    Otherwise, it runs daily at 03:00.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    if interval_seconds:
        scheduler.add_job(run_predictive_cycle, "interval", seconds=interval_seconds, id="predictive_cycle_test")
        log_manager.info(f"[PredictiveScheduler] Scheduler started in test mode. Running every {interval_seconds} seconds.")
    else:
        scheduler.add_job(run_predictive_cycle, "cron", hour=3, minute=0, id="predictive_cycle_nightly")
        log_manager.info("[PredictiveScheduler] Nightly predictive scheduler started for 03:00 UTC.")
        
    scheduler.start()
    
    try:
        # Keep the script running
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        log_manager.info("[PredictiveScheduler] Shutting down scheduler...")
        scheduler.shutdown()
        log_manager.info("[PredictiveScheduler] Scheduler stopped.")

if __name__ == '__main__':
    # For direct testing of the scheduler
    # e.g., python orchestrator/predictive_scheduler.py
    asyncio.run(start_predictive_scheduler(interval_seconds=30))
