# path: backend/api/stage_controller.py
# version: UI-v1.2
"""
Controls stage playback via TTS + OSC through FastAPI endpoints and WebSocket.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from modules.stage_director import StageDirector
from modules.script_parser import ScriptParser
from modules.tts_manager import TTSManager
from modules.osc_bridge import OSCBridge
from modules.log_manager import log_manager
import asyncio
import json
import time
import os

router = APIRouter()

# Global instance of StageDirector
# This will be initialized once and reused across requests
# For now, we'll instantiate it directly. In a larger app,
# dependency injection might be used.
tts_manager = TTSManager()
osc_bridge = OSCBridge()
director = StageDirector(tts=tts_manager, osc=osc_bridge)

# Store active WebSocket connections
active_connections: list[WebSocket] = []

@router.post("/api/stage/play")
async def play_stage():
    log_manager.info("[StageController] Play request received.")
    # In a real scenario, you might want to pass the timeline path dynamically
    # For now, it's hardcoded as per the spec.
    asyncio.create_task(director.play_timeline("data/timeline.json"))
    return {"status": "playing"}

@router.post("/api/stage/stop")
async def stop_stage():
    log_manager.info("[StageController] Stop request received.")
    # Future: Implement graceful stop in StageDirector
    # For now, we'll just send a stop signal to connected UIs
    for connection in active_connections:
        try:
            await connection.send_json({"type": "status", "status": "stopped"})
        except WebSocketDisconnect:
            pass # Client already disconnected
    return {"status": "stopped"}

@router.get("/api/stage/timeline")
async def get_timeline():
    log_manager.info("[StageController] Timeline request received.")
    timeline_path = "data/timeline.json"
    if not os.path.exists(timeline_path):
        # Generate timeline if it doesn't exist
        script_parser = ScriptParser()
        dummy_script_path = "data/script.json"
        if not os.path.exists(dummy_script_path):
            # Create a dummy script if it doesn't exist
            dummy_script_content = {
              "title": "Test Stage",
              "scenes": [
                {
                  "id": 1,
                  "character": "Shiroi",
                  "emotion": "joy",
                  "text": "こんにちは、瑞希。今日はシステムのデモを始めるね。",
                  "duration": 4.2
                },
                {
                  "id": 2,
                  "character": "Mizuki",
                  "emotion": "calm",
                  "text": "よろしくねシロイ、準備はできてる？",
                  "emotion": "calm",
                  "duration": 3.5
                }
              ]
            }
            os.makedirs(os.path.dirname(dummy_script_path), exist_ok=True)
            with open(dummy_script_path, "w", encoding="utf-8") as f:
                json.dump(dummy_script_content, f, indent=2, ensure_ascii=False)
        
        script_data = script_parser.load_script(dummy_script_path)
        timeline = script_parser.parse(script_data)
        script_parser.export_timeline(timeline_path)
        log_manager.info("[StageController] Generated timeline from dummy script.")
        return timeline
    
    try:
        with open(timeline_path, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)
        return timeline_data
    except Exception as e:
        log_manager.error(f"[StageController] Failed to load timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load timeline data.")

@router.websocket("/api/stage/ws")
async def stage_ws(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    log_manager.info("[StageController] WebSocket client connected.")
    try:
        while True:
            # This loop keeps the connection alive.
            # Actual progress updates will be pushed from StageDirector.
            await ws.receive_text() # Expect to receive messages to keep connection open, or just wait
    except WebSocketDisconnect:
        log_manager.info("[StageController] WebSocket client disconnected.")
    except Exception as e:
        log_manager.error(f"[StageController] WebSocket error: {e}", exc_info=True)
    finally:
        active_connections.remove(ws)
        log_manager.info("[StageController] WebSocket connection closed.")

# Need to modify StageDirector to push updates to active_connections
# This will be done in a later step or as part of Phase 5.
# For now, the WebSocket will just keep the connection open.
