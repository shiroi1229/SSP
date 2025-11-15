# path: modules/stage_director.py
# version: UI-v1.2
"""
Controls synchronized playback of TTS + OSC based on a parsed script timeline.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_manager import log_manager
from modules.tts_manager import TTSManager
from modules.osc_bridge import OSCBridge


class StageDirector:
    """Coordinates TTS and OSC playback according to timeline events."""

    def __init__(self, tts: TTSManager = None, osc: OSCBridge = None):
        self.tts = tts or TTSManager()
        self.osc = osc or OSCBridge()
        self.stage_log_dir = "logs/stage_logs"
        self.timeline_archive_dir = Path("data/stage_runs")
        os.makedirs(self.stage_log_dir, exist_ok=True)
        self.timeline_archive_dir.mkdir(parents=True, exist_ok=True)

    async def play_timeline(self, timeline_path: str, *, label: str | None = None, tags: list[str] | None = None):
        """Main function — load timeline JSON and execute it sequentially."""
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                timeline = json.load(f)
            log_manager.info(f"[StageDirector] Loaded timeline with {len(timeline)} events.")
        except Exception as e:
            log_manager.error(f"[StageDirector] Failed to load timeline: {e}", exc_info=True)
            return

        stage_log = []
        start_time = datetime.now().timestamp()

        for idx, event in enumerate(timeline):
            try:
                text = event["text"]
                emotion = event.get("emotion", "neutral")
                duration = event.get("duration", 3.0)

                log_manager.info(f"[StageDirector] ({idx+1}/{len(timeline)}) {event['character']} → {emotion}")
                await asyncio.gather(
                    self.tts.speak(text, emotion),
                    self.osc.send_emotion(emotion)
                )

                # Log execution
                stage_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "character": event["character"],
                    "emotion": emotion,
                    "text": text,
                    "duration": duration
                })
                await asyncio.sleep(duration)

            except Exception as e:
                log_manager.error(f"[StageDirector] Error executing event {idx}: {e}", exc_info=True)

        total_time = datetime.now().timestamp() - start_time
        log_manager.info(f"[StageDirector] Timeline playback completed in {total_time:.2f}s.")
        self._record_stage_log(stage_log, source_path=timeline_path, label=label, tags=tags or [])
        self._archive_timeline(timeline_path, stage_log, label=label, tags=tags or [])

    def _record_stage_log(self, stage_log, *, source_path: str | None = None, label: str | None = None, tags: list[str] | None = None):
        """Saves execution logs to a timestamped file for replay."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.stage_log_dir, f"stage_run_{timestamp}.json")
        payload = {
            "metadata": {
                "source_timeline": source_path,
                "label": label,
                "tags": tags or [],
                "event_count": len(stage_log),
            },
            "events": stage_log,
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[StageDirector] Stage run log saved to {path}")
        except Exception as e:
            log_manager.error(f"[StageDirector] Failed to save stage log: {e}", exc_info=True)

    def _archive_timeline(self, timeline_path: str, stage_log: list, *, label: str | None = None, tags: list[str] | None = None):
        """Save a combined snapshot of the timeline and resulting log for later UI playback."""
        if not os.path.exists(timeline_path):
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{Path(timeline_path).stem}_{timestamp}.json"
        archive_path = self.timeline_archive_dir / archive_name
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                timeline = json.load(f)
            snapshot = {
                "timeline_source": timeline_path,
                "label": label,
                "tags": tags or [],
                "captured_at": datetime.now().isoformat(),
                "timeline": timeline,
                "log_events": stage_log,
            }
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[StageDirector] Timeline archive saved to {archive_path}")
        except Exception as e:
            log_manager.error(f"[StageDirector] Failed to archive timeline: {e}", exc_info=True)

    async def play_timeline_from_memory(self, timeline: list):
        """Play a given timeline already loaded in memory (for replay)."""
        log_manager.info(f"[StageDirector] Playing timeline from memory with {len(timeline)} events.")
        for idx, event in enumerate(timeline):
            try:
                text = event["text"]
                emotion = event.get("emotion", "neutral")
                duration = event.get("duration", 3.0)

                log_manager.info(f"[StageDirector] (Replay {idx+1}/{len(timeline)}) {event['character']} → {emotion}")
                await asyncio.gather(
                    self.tts.speak(text, emotion),
                    self.osc.send_emotion(emotion) # Corrected from send_expression
                )
                await asyncio.sleep(duration)
            except Exception as e:
                log_manager.error(f"[StageDirector] Error replaying event {idx}: {e}", exc_info=True)
        log_manager.info("[StageDirector] Timeline replay from memory completed.")


if __name__ == "__main__":
    # Ensure data/timeline.json exists from Phase 1
    # For testing, you might want to run script_parser.py first
    # python modules/script_parser.py
    
    director = StageDirector()
    asyncio.run(director.play_timeline("data/timeline.json"))
