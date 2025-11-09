# path: backend/main.py
# version: v0.30
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import persona_state, logs_recent, evaluate, context, analyze_sessions, sessions, chat, get_context, status, emotion, tts, osc, roadmap, roadmap_tree, dashboard_ws, system_health
from backend.api import system_forecast # Import the new forecast router
from backend.api.logs import recent
from backend.api.logs import roadmap_sync # Import the new roadmap_sync router
from backend.api.logs import predictive_self_correction # Import the new predictive_self_correction router
from backend.api.ws_forecast import router as ws_forecast_router
from backend.api.stage_controller import router as stage_controller_router # Import the new stage_controller router
from backend.api.stage_replay import router as stage_replay_router # Import the new stage_replay router
from backend.api.stage_memory import router as stage_memory_router # Import the new stage_memory router
from backend.api.persona_routes import router as persona_routes_router # Import the new persona_routes router

from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.insight_monitor import InsightMonitor
from modules.log_manager import log_manager

app = FastAPI(title="Shiroi System Platform", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global instances for ContextManager and InsightMonitor
# These will be initialized on startup
global_context_manager: ContextManager = None
global_insight_monitor: InsightMonitor = None

@app.on_event("startup")
async def startup_event():
    global global_context_manager, global_insight_monitor
    log_manager.info("Initializing global ContextManager and InsightMonitor...")
    global_context_manager = ContextManager()
    # RecoveryPolicyManager is a dependency for InsightMonitor
    # For now, we'll create a dummy one if not already managed elsewhere
    # In a full system, this would be a properly configured instance
    recovery_policy_manager = RecoveryPolicyManager() 
    global_insight_monitor = InsightMonitor(global_context_manager, recovery_policy_manager)
    
    # Assign the global ContextManager to the system_health module
    system_health.context_manager_instance = global_context_manager
    log_manager.info("Global ContextManager and InsightMonitor initialized.")


# ✅ router登録（prefix指定）
app.include_router(persona_state.router, prefix="/api")
app.include_router(logs_recent.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api") # ✅ evaluate.router を追加
app.include_router(context.router, prefix="/api") # Add prefix here
app.include_router(analyze_sessions.router) # No prefix, already in router
app.include_router(sessions.router, prefix="/api") # Add prefix here
app.include_router(chat.router) # No prefix, already in router
app.include_router(get_context.router, prefix="/api")
app.include_router(recent.router, prefix="/api")
app.include_router(roadmap_sync.router, prefix="/api") # Include the new roadmap_sync router
app.include_router(predictive_self_correction.router, prefix="/api") # Include the new predictive_self_correction router
app.include_router(status.router, prefix="/api")
app.include_router(emotion.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(osc.router, prefix="/api")
app.include_router(roadmap_tree.router) # No prefix, already in router
app.include_router(roadmap.router) # No prefix, already in router
app.include_router(dashboard_ws.router, prefix="/api") # Include the dashboard_ws router
app.include_router(system_health.router, prefix="/api")
app.include_router(system_forecast.router, prefix="/api")
app.include_router(ws_forecast_router)
app.include_router(stage_controller_router)
app.include_router(stage_replay_router)
app.include_router(stage_memory_router)
app.include_router(persona_routes_router)

# Test comment for ImpactAnalyzer
@app.get("/")
def read_root():
    return {"message": "SSP API root active"}
