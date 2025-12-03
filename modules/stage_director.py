"""Controls synchronized playback of TTS + OSC based on parsed stage timelines."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.emotion_engine import EmotionEngine
from modules.log_manager import log_manager
from modules.memory_store import MemoryStore
from modules.osc_bridge import OSCBridge
from modules.tts_manager import TTSManager


class StageDirector:
    """Coordinates TTS/OSC playback and pushes progress updates to dashboard UI."""

    def __init__(
        self,
        tts: TTSManager | None = None,
        osc: OSCBridge | None = None,
        progress_callback: Callable[[Dict[str, Any]], Awaitable[None]] | None = None,
    ):
        self.tts = tts or TTSManager()
        self.osc = osc or OSCBridge()
        self.stage_log_dir = "logs/stage_logs"
        self.timeline_archive_dir = Path("data/stage_runs")
        self.checkpoint_dir = Path("logs/stage_checkpoints")
        os.makedirs(self.stage_log_dir, exist_ok=True)
        self.timeline_archive_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.emotion_engine = EmotionEngine()
        self.memory_store = MemoryStore()

    @staticmethod
    def _log_step(step: str, status: str, *, duration_ms: float | None = None, items: int | None = None, error: str | None = None, extra: Dict[str, Any] | None = None) -> None:
        payload: Dict[str, Any] = {"step": step, "status": status}
        if duration_ms is not None:
            payload["duration_ms"] = round(duration_ms, 2)
        if items is not None:
            payload["items"] = items
        if error:
            payload["error"] = error
        if extra:
            payload.update(extra)
        log_manager.info(f"[StageDirector] {step} {status}", extra={"extra_data": payload})

    def _checkpoint_path(self, session_key: str) -> Path:
        return self.checkpoint_dir / f"{session_key}.json"

    def _load_checkpoint(self, session_key: str) -> Dict[str, Any]:
        path = self._checkpoint_path(session_key)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._log_step("checkpoint_load", "ok", extra={"session": session_key, "next_event_index": data.get("next_event_index", 0)})
            return data
        except Exception as exc:  # pragma: no cover - safeguard
            self._log_step("checkpoint_load", "error", error=str(exc), extra={"session": session_key})
            return {}

    def _save_checkpoint(self, session_key: str, next_event_index: int, *, last_error: str | None = None) -> None:
        payload = {
            "session": session_key,
            "next_event_index": next_event_index,
            "updated_at": datetime.now().isoformat(),
            "last_error": last_error,
        }
        try:
            with open(self._checkpoint_path(session_key), "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self._log_step("checkpoint_save", "ok", extra={"session": session_key, "next_event_index": next_event_index})
        except Exception as exc:  # pragma: no cover - safeguard
            self._log_step("checkpoint_save", "error", error=str(exc), extra={"session": session_key, "next_event_index": next_event_index})

    def _clear_checkpoint(self, session_key: str) -> None:
        path = self._checkpoint_path(session_key)
        if path.exists():
            try:
                path.unlink()
                self._log_step("checkpoint_clear", "ok", extra={"session": session_key})
            except Exception as exc:  # pragma: no cover - safeguard
                self._log_step("checkpoint_clear", "error", error=str(exc), extra={"session": session_key})

    async def play_timeline(self, timeline_path: str, *, label: str | None = None, tags: List[str] | None = None, max_retries: int = 2):
        """Load a timeline JSON file and execute it sequentially."""
        load_started = time.perf_counter()
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                timeline = json.load(f)
            duration_ms = (time.perf_counter() - load_started) * 1000
            self._log_step("timeline_load", "ok", duration_ms=duration_ms, items=len(timeline), extra={"timeline_path": timeline_path})
        except Exception as exc:
            self._log_step("timeline_load", "error", duration_ms=(time.perf_counter() - load_started) * 1000, error=str(exc), extra={"timeline_path": timeline_path})
            log_manager.error(f"[StageDirector] Failed to load timeline: {exc}", exc_info=True)
            return

        stage_log: List[Dict[str, Any]] = []
        start_time = datetime.now().timestamp()
        elapsed = 0.0
        session_key = Path(timeline_path).stem
        checkpoint = self._load_checkpoint(session_key)
        resume_index = int(checkpoint.get("next_event_index", 0))
        if resume_index:
            self._log_step("timeline_resume", "ok", extra={"session": session_key, "resume_from": resume_index})
        await self._notify_clients({"type": "status", "status": "playing", "timeline": session_key})

        for idx, event in enumerate(timeline[resume_index:], start=resume_index):
            try:
                event_started = time.perf_counter()
                text = event.get("text", "")
                duration = float(event.get("duration", 3.0))
                emotion_payload = self._prepare_emotion_payload(event)
                dominant_emotion = emotion_payload["dominant_emotion"]

                attempts = 0
                last_error: str | None = None
                while attempts <= max_retries:
                    attempts += 1
                    step_start = time.perf_counter()
                    try:
                        tts_result, osc_result = await asyncio.gather(
                            self.tts.speak(text, emotion_payload),
                            self.osc.send_emotion(dominant_emotion.capitalize()),
                        )
                        self._log_step(
                            "event_execute",
                            "ok",
                            duration_ms=(time.perf_counter() - step_start) * 1000,
                            items=1,
                            extra={
                                "event_index": idx,
                                "character": event.get("character"),
                                "emotion": dominant_emotion,
                                "attempt": attempts,
                                "timeline_size": len(timeline),
                            },
                        )
                        last_error = None
                        break
                    except Exception as exc:  # retry-able block
                        last_error = str(exc)
                        self._log_step(
                            "event_execute",
                            "retrying" if attempts <= max_retries else "failed",
                            duration_ms=(time.perf_counter() - step_start) * 1000,
                            items=1,
                            error=last_error,
                            extra={
                                "event_index": idx,
                                "character": event.get("character"),
                                "attempt": attempts,
                                "max_retries": max_retries,
                            },
                        )
                        if attempts > max_retries:
                            raise
                        await asyncio.sleep(min(1.0 * attempts, 5.0))

                stage_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "character": event.get("character"),
                    "emotion": dominant_emotion,
                    "text": text,
                    "duration": duration,
                    "audio_path": (tts_result or {}).get("audio_path") if isinstance(tts_result, dict) else None,
                    "emotion_vector": emotion_payload["emotion_vector"],
                    "osc_payload": osc_result,
                }
                stage_log.append(stage_entry)
                await self._persist_stage_event(session_key, idx, stage_entry)
                self._save_checkpoint(session_key, idx + 1)

                elapsed += duration
                await self._notify_clients(
                    {
                        "type": "progress",
                        "index": idx,
                        "time": elapsed,
                        "emotion": dominant_emotion,
                        "vector": emotion_payload["emotion_vector"],
                        "text": text,
                        "audioPath": stage_entry["audio_path"],
                    }
                )
                self._log_step(
                    "event_complete",
                    "ok",
                    duration_ms=(time.perf_counter() - event_started) * 1000,
                    items=1,
                    extra={"event_index": idx, "elapsed_schedule_s": elapsed},
                )
                await asyncio.sleep(duration)
            except Exception as exc:
                self._save_checkpoint(session_key, idx, last_error=str(exc))
                self._log_step(
                    "event_complete",
                    "error",
                    error=str(exc),
                    extra={"event_index": idx, "timeline": session_key},
                )
                log_manager.error(f"[StageDirector] Error executing event {idx}: {exc}", exc_info=True)
                break

        total_time = datetime.now().timestamp() - start_time
        self._clear_checkpoint(session_key)
        self._log_step("timeline_complete", "ok", duration_ms=total_time * 1000, items=len(stage_log), extra={"timeline": session_key})
        self._record_stage_log(stage_log, source_path=timeline_path, label=label, tags=tags or [])
        self._archive_timeline(timeline_path, stage_log, label=label, tags=tags or [])
        await self._notify_clients({"type": "status", "status": "stopped", "timeline": session_key})

    def _record_stage_log(self, stage_log: List[Dict[str, Any]], *, source_path: str | None = None, label: str | None = None, tags: List[str] | None = None):
        """Save execution logs to a timestamped file for replay."""
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
        except Exception as exc:
            log_manager.error(f"[StageDirector] Failed to save stage log: {exc}", exc_info=True)

    def _archive_timeline(self, timeline_path: str, stage_log: List[Dict[str, Any]], *, label: str | None = None, tags: List[str] | None = None):
        """Persist a combined snapshot of the timeline + resulting execution log."""
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
        except Exception as exc:
            log_manager.error(f"[StageDirector] Failed to archive timeline: {exc}", exc_info=True)

    async def play_timeline_from_memory(self, timeline: List[Dict[str, Any]]):
        """Play a given timeline already loaded in memory (for replay/testing)."""
        log_manager.info(f"[StageDirector] Playing timeline from memory with {len(timeline)} events.")
        for idx, event in enumerate(timeline):
            try:
                text = event["text"]
                emotion = event.get("emotion", "neutral")
                duration = event.get("duration", 3.0)
                log_manager.info(f"[StageDirector] (Replay {idx+1}/{len(timeline)}) {event['character']} → {emotion}")
                await asyncio.gather(
                    self.tts.speak(text, emotion),
                    self.osc.send_emotion(emotion),
                )
                await asyncio.sleep(duration)
            except Exception as exc:
                log_manager.error(f"[StageDirector] Error replaying event {idx}: {exc}", exc_info=True)
        log_manager.info("[StageDirector] Timeline replay from memory completed.")

    def _prepare_emotion_payload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        hint = event.get("emotion")
        text = event.get("text", "")
        analysis = self.emotion_engine.analyze_emotion(text, hint)
        analysis["emotion_tags"] = [analysis["dominant_emotion"].capitalize()]
        return analysis

    async def _notify_clients(self, payload: Dict[str, Any]) -> None:
        if not self.progress_callback:
            return
        try:
            await self.progress_callback(payload)
        except Exception as exc:  # pragma: no cover - safety path
            log_manager.error(f"[StageDirector] Failed to notify clients: {exc}", exc_info=True)

    async def _persist_stage_event(self, session_key: str, iteration: int, stage_entry: Dict[str, Any]) -> None:
        record = {
            "session_id": f"stage::{session_key}",
            "user_input": stage_entry.get("text", ""),
            "answer": stage_entry.get("text", ""),
            "rating": 0,
            "feedback": "",
            "audio_path": stage_entry.get("audio_path"),
            "emotion_vector": stage_entry.get("emotion_vector"),
            "osc_payload": stage_entry.get("osc_payload"),
            "emotion_tags": [stage_entry.get("emotion", "neutral")],
        }
        self.memory_store.save(record, iteration=iteration + 1)


if __name__ == "__main__":
    director = StageDirector()
    asyncio.run(director.play_timeline("data/timeline.json"))
