# path: modules/stage_recorder.py
# version: UI-v1.2
"""
Records and replays stage execution logs for reproducible performance playback.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.stage_director import StageDirector
from modules.log_manager import log_manager


class StageRecorder:
    """Handles recording and replaying of stage performances."""

    def __init__(self):
        self.archive_dir = Path("data/stage_runs")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        # We instantiate a new director for replay tasks.
        # In a larger app, this might be a shared instance.
        self.director = StageDirector()

    def record_stage(self, timeline: list, run_id: str | None = None, *, source: str | None = None):
        """Save timeline and metadata for later replay."""
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.archive_dir / f"run_{run_id}.json"

        data = {
            "timeline_source": source,
            "label": None,
            "tags": [],
            "captured_at": datetime.now().isoformat(),
            "timeline": timeline,
            "log_events": [],
        }
        try:
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[StageRecorder] Recorded stage run: {archive_path}")
            return str(archive_path)
        except Exception as e:
            log_manager.error(f"[StageRecorder] Failed to record stage: {e}", exc_info=True)
            raise

    async def replay_stage(self, log_path: str):
        """Replay a recorded stage performance."""
        path = Path(log_path)
        if not path.is_absolute():
            path = self.archive_dir / path
        if not path.exists():
            log_manager.error(f"[StageRecorder] Log file not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            timeline = data.get("timeline", [])
            if not timeline:
                log_manager.error(f"[StageRecorder] Timeline missing in {path}")
                return
            log_manager.info(f"[StageRecorder] Replaying stage run from {path}")
            await self.director.play_timeline_from_memory(timeline)
        except Exception as e:
            log_manager.error(f"[StageRecorder] Failed to replay stage: {e}", exc_info=True)

    def list_logs(self):
        """Return a list of all recorded stage logs."""
        try:
            return sorted([f.name for f in self.archive_dir.glob("*.json")])
        except FileNotFoundError:
            log_manager.warning(f"[StageRecorder] Archive directory not found: {self.archive_dir}")
            return []
