# path: modules/osc_bridge.py
# version: v1
# OSC Bridge: EmotionタグをVTube Studioへ送信し、表情を制御する。
# 依存: python-osc

from pythonosc.udp_client import SimpleUDPClient
import os
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

    def send(self, address: str, value: float):
        """Sends a single OSC message."""
        if self.client:
            self.client.send_message(address, value)

    def send_emotion(self, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends OSC messages based on emotion data to control VTube Studio parameters.
        """
        if not self.client:
            return {"status": "error", "reason": "OSC client not initialized"}

        tags = emotion_data.get("emotion_tags", ["Neutral"])
        intensity = emotion_data.get("intensity", 0.5)
        
        # Reset all params first to avoid conflicting expressions
        self.send("/avatar/parameters/ParamSmile", 0.0)
        self.send("/avatar/parameters/ParamEyeOpen", 0.8) # Default open
        self.send("/avatar/parameters/ParamBrowAngle", 0.0)
        self.send("/avatar/parameters/ParamEyeForm", 0.0)

        primary_emotion = tags[0] if tags else "Neutral"

        # Set expression based on primary emotion
        if primary_emotion == "Joy":
            self.send("/avatar/parameters/ParamSmile", min(1.0, 0.4 + intensity * 0.6))
            self.send("/avatar/parameters/ParamEyeOpen", 1.0)
        elif primary_emotion == "Calm":
            self.send("/avatar/parameters/ParamSmile", 0.1 * intensity)
            self.send("/avatar/parameters/ParamEyeOpen", 0.7)
        elif primary_emotion == "Sad":
            self.send("/avatar/parameters/ParamEyeForm", -0.5 * intensity)
            self.send("/avatar/parameters/ParamBrowAngle", -0.2 * intensity)
            self.send("/avatar/parameters/ParamEyeOpen", 0.6)
        elif primary_emotion == "Angry":
            self.send("/avatar/parameters/ParamBrowAngle", 0.6 * intensity)
            self.send("/avatar/parameters/ParamEyeOpen", 0.7)
        elif primary_emotion == "Curious":
            self.send("/avatar/parameters/ParamEyeOpen", 0.9)
            self.send("/avatar/parameters/ParamSmile", 0.2 * intensity)
        else: # Neutral
            self.send("/avatar/parameters/ParamEyeOpen", 0.8)

        return {
            "status": "sent", 
            "host": self.host, 
            "port": self.port, 
            "emotion": primary_emotion,
            "intensity": intensity
        }
