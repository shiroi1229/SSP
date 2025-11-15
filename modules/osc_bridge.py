# path: modules/osc_bridge.py
# version: v1
# OSC Bridge: EmotionタグをVTube Studioへ送信し、表情を制御する。
# 依存: python-osc

from pythonosc.udp_client import SimpleUDPClient
import os
import asyncio
from typing import Dict, Any

class OSCBridge:
    def __init__(self, host: str | None = None, port: int | None = None):
        """Initializes the OSCBridge client."""
        self.host = host or os.getenv("OSC_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("OSC_PORT", 8001))
        try:
            self.client = SimpleUDPClient(self.host, self.port)
        except Exception as e:
            print(f"Could not create OSC client: {e}")
            self.client = None

    async def send(self, address: str, value: float):
        """Sends a single OSC message asynchronously."""
        if self.client:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.client.send_message, address, value)

    async def send_emotion(self, emotion: str) -> Dict[str, Any]:
        """
        Sends OSC messages based on emotion data to control VTube Studio parameters.
        Emotion is a string (e.g., "joy", "calm").
        """
        if not self.client:
            return {"status": "error", "reason": "OSC client not initialized"}

        # Convert string emotion to dictionary format
        emotion_data = {"emotion_tags": [emotion.capitalize()], "intensity": 0.7} # Default intensity
        
        tags = emotion_data.get("emotion_tags", ["Neutral"])
        intensity = emotion_data.get("intensity", 0.5)
        
        primary_emotion = tags[0] if tags else "Neutral"

        # Create a list of tasks to run in parallel
        tasks = [
            self.send("/avatar/parameters/ParamSmile", 0.0),
            self.send("/avatar/parameters/ParamEyeOpen", 0.8),
            self.send("/avatar/parameters/ParamBrowAngle", 0.0),
            self.send("/avatar/parameters/ParamEyeForm", 0.0)
        ]

        # Set expression based on primary emotion
        if primary_emotion == "Joy":
            tasks.append(self.send("/avatar/parameters/ParamSmile", min(1.0, 0.4 + intensity * 0.6)))
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 1.0))
        elif primary_emotion == "Calm":
            tasks.append(self.send("/avatar/parameters/ParamSmile", 0.1 * intensity))
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 0.7))
        elif primary_emotion == "Sad":
            tasks.append(self.send("/avatar/parameters/ParamEyeForm", -0.5 * intensity))
            tasks.append(self.send("/avatar/parameters/ParamBrowAngle", -0.2 * intensity))
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 0.6))
        elif primary_emotion == "Angry":
            tasks.append(self.send("/avatar/parameters/ParamBrowAngle", 0.6 * intensity))
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 0.7))
        elif primary_emotion == "Curious":
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 0.9))
            tasks.append(self.send("/avatar/parameters/ParamSmile", 0.2 * intensity))
        else: # Neutral
            tasks.append(self.send("/avatar/parameters/ParamEyeOpen", 0.8))

        await asyncio.gather(*tasks)

        return {
            "status": "sent", 
            "host": self.host, 
            "port": self.port, 
            "emotion": primary_emotion,
            "intensity": intensity
        }

