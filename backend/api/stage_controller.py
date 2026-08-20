"""Stage playback API for orchestrating TTS + OSC pipeline."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from modules.log_manager import log_manager
from modules.osc_bridge import OSCBridge
from modules.script_parser import ScriptParser
from modules.stage_director import StageDirector
from modules.tts_manager import TTSManager

router = APIRouter()

tts_manager = TTSManager()
osc_bridge = OSCBridge()

active_connections: List[WebSocket] = []


async def broadcast_progress(payload: Dict[str, Any]):
    stale: List[WebSocket] = []
    for connection in list(active_connections):
        try:
            await connection.send_json(payload)
        except WebSocketDisconnect:
            stale.append(connection)
        except RuntimeError:
            stale.append(connection)
    for connection in stale:
        if connection in active_connections:
            active_connections.remove(connection)


director = StageDirector(tts=tts_manager, osc=osc_bridge, progress_callback=broadcast_progress)


@router.post("/api/stage/play")
async def play_stage():
    log_manager.info("[StageController] Play request received.")
    asyncio.create_task(director.play_timeline("data/timeline.json"))
    return {"status": "playing"}


@router.post("/api/stage/stop")
async def stop_stage():
    log_manager.info("[StageController] Stop request received.")
    await broadcast_progress({"type": "status", "status": "stopped"})
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
