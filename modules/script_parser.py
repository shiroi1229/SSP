# path: modules/script_parser.py
# version: UI-v1.2
"""
Parses JSON-based stage scripts into timeline events for synchronized TTS + OSC playback.
"""

import os
import sys
import json
from typing import List, Dict, Any

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_manager import log_manager


class ScriptParser:
    """Parses stage scripts and produces timeline events."""

    def __init__(self):
        self.timeline: List[Dict[str, Any]] = []

    def load_script(self, file_path: str) -> dict:
        """Load a JSON script file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log_manager.info(f"[ScriptParser] Script loaded: {file_path}")
            return data
        except Exception as e:
            log_manager.error(f"[ScriptParser] Failed to load script: {e}", exc_info=True)
            raise

    def parse(self, script_data: dict) -> List[Dict[str, Any]]:
        """
        Parse the script JSON into a timeline.
        Each scene is mapped to a TimelineEvent with time offsets.
        """
        timeline = []
        current_time = 0.0
        for scene in script_data.get("scenes", []):
            event = {
                "time": round(current_time, 2),
                "character": scene.get("character", "Unknown"),
                "text": scene.get("text", ""),
                "emotion": scene.get("emotion", "neutral"),
                "duration": float(scene.get("duration", 3.0))
            }
            timeline.append(event)
            current_time += event["duration"]
        self.timeline = timeline
        log_manager.info(f"[ScriptParser] Parsed {len(timeline)} timeline events.")
        return timeline

    def export_timeline(self, output_path: str):
        """Save parsed timeline to JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.timeline, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[ScriptParser] Timeline exported to {output_path}")
        except Exception as e:
            log_manager.error(f"[ScriptParser] Failed to export timeline: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    # Create a dummy script.json for testing
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
    dummy_script_path = "data/script.json"
    os.makedirs(os.path.dirname(dummy_script_path), exist_ok=True)
    with open(dummy_script_path, "w", encoding="utf-8") as f:
        json.dump(dummy_script_content, f, indent=2, ensure_ascii=False)
    
    parser = ScriptParser()
    data = parser.load_script(dummy_script_path)
    timeline = parser.parse(data)
    parser.export_timeline("data/timeline.json")
    print(f"Timeline generated and saved to data/timeline.json. Check its content.")
