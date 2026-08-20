import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
import psutil # For system metrics

# Import actual SSP modules
from modules.persona_manager import get_current_persona_state
from modules.metacognition import get_latest_introspection_log, get_cognitive_graph_data

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Any

router = APIRouter()

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {websocket.client}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection) # Clean up disconnected clients

manager = ConnectionManager()

# --- Real Data Functions ---
async def get_persona_state_data(): # Changed to async again
    persona_state = await get_current_persona_state() # Re-added await
    cognitive_graph = get_cognitive_graph_data() # This is synchronous
    
    return {
        "type": "persona_state",
        "timestamp": datetime.now().isoformat(),
        "emotion": persona_state.get("emotion", "unknown"), # Simplified emotion string
        "emotion_state": persona_state.get("detailed_emotion_state", {}), # Detailed emotion state for UI
        "harmony": persona_state.get("harmony_score", 0.0),
        "cognitive_graph": cognitive_graph
    }

def get_introspection_log_data(): # Changed to synchronous
    log_entry = get_latest_introspection_log() # Removed await
    return {
        "type": "introspection_log",
        "timestamp": datetime.now().isoformat(),
        "log_entry": log_entry.get("log_entry", "No log entry") if isinstance(log_entry, dict) else str(log_entry)
    }

def get_system_metrics_data(): # Changed to synchronous
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()
    
    metrics = {
        "type": "system_metrics",
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_info.percent, 2),
        "disk_percent": round(disk_info.percent, 2),
        "network_io_sent": net_io.bytes_sent,
        "network_io_recv": net_io.bytes_recv,
    }
    return metrics

# --- WebSocket Endpoint ---
@router.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send persona state
            persona_state_data = await get_persona_state_data() # Added await
            await manager.send_personal_message(json.dumps(persona_state_data), websocket)

            # Send introspection log
            introspection_log_data = get_introspection_log_data() # Removed await
            await manager.send_personal_message(json.dumps(introspection_log_data), websocket)

            # Send system metrics
            system_metrics_data = get_system_metrics_data() # Removed await
            await manager.send_personal_message(json.dumps(system_metrics_data), websocket)

            await asyncio.sleep(1) # Send updates every 1 second
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket {websocket.client} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error for {websocket.client}: {e}", exc_info=True)
        manager.disconnect(websocket)

# --- Emotion WebSocket Endpoint ---
@router.websocket("/ws/emotion")
async def websocket_emotion_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Fetch current emotion state from persona_manager
            persona_state = await get_current_persona_state()
            current_emotion = persona_state.get("detailed_emotion_state", {
                "joy": 0.5, "anger": 0.1, "sadness": 0.2,
                "happiness": 0.7, "fear": 0.05, "calm": 0.8
            }) # Fallback to placeholder if not found

            await manager.send_personal_message(json.dumps(current_emotion), websocket)
            await asyncio.sleep(0.5) # Send updates more frequently for emotions
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Emotion WebSocket {websocket.client} disconnected.")
    except Exception as e:
        logger.error(f"Emotion WebSocket error for {websocket.client}: {e}", exc_info=True)
        manager.disconnect(websocket)