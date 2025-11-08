# path: backend/main.py
# version: v0.30
from fastapi import FastAPI
from backend.api import persona_state, logs_recent, evaluate, context, analyze_sessions, sessions, chat, get_context, status, emotion, tts, osc, roadmap
from backend.api.logs import recent
from backend.api.logs import roadmap_sync # Import the new roadmap_sync router

app = FastAPI(title="Shiroi System Platform", version="0.1.0")

# ✅ router登録（prefix指定しない）
app.include_router(persona_state.router)
app.include_router(logs_recent.router)
app.include_router(evaluate.router) # ✅ evaluate.router を追加
app.include_router(context.router)
app.include_router(analyze_sessions.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(get_context.router)
app.include_router(recent.router)
app.include_router(roadmap_sync.router) # Include the new roadmap_sync router
app.include_router(status.router)
app.include_router(emotion.router)
app.include_router(tts.router)
app.include_router(osc.router)
app.include_router(roadmap.router) # Include the new roadmap router

# Test comment for ImpactAnalyzer
@app.get("/")
def read_root():
    return {"message": "SSP API root active"}
