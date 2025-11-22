# path: backend/main.py
# version: v0.30
# purpose: FastAPIアプリの初期化・lifespanでの依存初期化・全APIルータの集約
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import persona_state, logs_recent, evaluate, context, analyze_sessions, knowledge, sessions, chat, get_context, status, emotion, tts, osc, roadmap, roadmap_tree, dashboard_ws, system_health, modules, collective_mind, robustness_firewall, robustness_self_healing, robustness_loop_health, robustness_loop_config, robustness_load_balancer, robustness_recovery, robustness_akashic, robustness_resilience, robustness_luminous, awareness, internal_dialogue, security
from backend.api import timeline_restore, context_rollback, causal_trace, causal_verify, causal_events, causal_insight, causal_report, meta_causal_feedback, meta_causal_bias, auto_actions, meta_causal_bias_history, meta_causal_report, meta_optimizer, world_timeline
from backend.api import system_forecast # Import the new forecast router
from backend.api.cluster import router as cluster_router
from backend.api.system import router as system_router
from backend.api.continuum.state import router as continuum_state_router
from backend.api.continuum.stream import router as continuum_stream_router
from backend.api.metrics_v0_1 import router as metrics_v0_1_router
from backend.api.error_summary import router as error_summary_router
from backend.api.module_stats import router as module_stats_router
from backend.api.recovery import router as recovery_router
from backend.api.logs import recent
from backend.api.logs import roadmap_sync # Import the new roadmap_sync router
from backend.api.logs import predictive_self_correction # Import the new predictive_self_correction router
from backend.api.ws_forecast import router as ws_forecast_router
from backend.api.stage_controller import router as stage_controller_router # Import the new stage_controller router
from backend.api.stage_replay import router as stage_replay_router # Import the new stage_replay router
from backend.api.stage_memory import router as stage_memory_router # Import the new stage_memory router
from backend.api.stage_runs import router as stage_runs_router
from backend.api.persona_routes import router as persona_routes_router # Import the new persona_routes router
from backend.api import meta_contracts

from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.insight_monitor import InsightMonitor
from modules.log_manager import log_manager
from modules.api_interface import router as insight_router
from backend.middleware.metrics_logger import setup_metrics_middleware

# Configure logging once at the application's entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_manager.info("Initializing ContextManager and InsightMonitor (app.state)...")
    ctx = ContextManager()
    rpm = RecoveryPolicyManager()
    insight = InsightMonitor(ctx, rpm)
    app.state.context_manager = ctx
    app.state.insight_monitor = insight
    log_manager.info("Context services registered in app.state.")
    yield


app = FastAPI(title="Shiroi System Platform", version="0.1.0", lifespan=lifespan)
setup_metrics_middleware(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

 

 


# ✁Erouter登録�E�Erefix持E��！E# app.include_router(persona_state.router, prefix="/api")
app.include_router(logs_recent.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api")
app.include_router(context.router, prefix="/api")
app.include_router(analyze_sessions.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(get_context.router, prefix="/api")
app.include_router(recent.router, prefix="/api")
app.include_router(roadmap_sync.router, prefix="/api")
app.include_router(predictive_self_correction.router, prefix="/api")
app.include_router(module_stats_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(module_stats_router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(emotion.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(osc.router, prefix="/api")
app.include_router(roadmap_tree.router, prefix="/api")
app.include_router(roadmap.router, prefix="/api")
app.include_router(dashboard_ws.router, prefix="/api")
app.include_router(system_forecast.router, prefix="/api")
app.include_router(system_health.router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(continuum_state_router, prefix="/api")
app.include_router(continuum_stream_router, prefix="/api")
app.include_router(metrics_v0_1_router, prefix="/api")
app.include_router(error_summary_router, prefix="/api")
app.include_router(cluster_router, prefix="/api")
app.include_router(ws_forecast_router, prefix="/api") # Assuming this should also be under /api
app.include_router(stage_controller_router, prefix="/api")
app.include_router(stage_replay_router, prefix="/api")
app.include_router(stage_memory_router, prefix="/api")
app.include_router(stage_runs_router, prefix="/api")
app.include_router(persona_routes_router, prefix="/api")
app.include_router(modules.router, prefix="/api")
app.include_router(insight_router, prefix="/api")
app.include_router(collective_mind.router, prefix="/api")
app.include_router(awareness.router, prefix="/api")
app.include_router(internal_dialogue.router, prefix="/api")
app.include_router(robustness_firewall.router, prefix="/api")
app.include_router(robustness_self_healing.router, prefix="/api")
app.include_router(robustness_loop_health.router, prefix="/api")
app.include_router(robustness_loop_config.router, prefix="/api")
app.include_router(robustness_load_balancer.router, prefix="/api")
app.include_router(robustness_recovery.router, prefix="/api")
app.include_router(robustness_akashic.router, prefix="/api")
app.include_router(robustness_resilience.router, prefix="/api")
app.include_router(robustness_luminous.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(timeline_restore.router, prefix="/api")
app.include_router(context_rollback.router, prefix="/api")
app.include_router(causal_trace.router, prefix="/api")
app.include_router(causal_verify.router, prefix="/api")
app.include_router(causal_events.router, prefix="/api")
app.include_router(causal_insight.router, prefix="/api")
app.include_router(causal_report.router, prefix="/api")
app.include_router(meta_causal_feedback.router, prefix="/api")
app.include_router(meta_causal_bias.router, prefix="/api")
app.include_router(meta_causal_bias_history.router, prefix="/api")
app.include_router(meta_causal_report.router, prefix="/api")
app.include_router(auto_actions.router, prefix="/api")
app.include_router(meta_optimizer.router, prefix="/api")
app.include_router(world_timeline.router, prefix="/api")
app.include_router(meta_contracts.router, prefix="/api")

# Test comment for ImpactAnalyzer
@app.get("/")
def read_root():
    return {"message": "SSP API root active"}

import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
