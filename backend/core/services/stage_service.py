from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

from modules.log_manager import log_manager
from modules.osc_bridge import OSCBridge
from modules.script_parser import ScriptParser
from modules.stage_director import StageDirector
from modules.tts_manager import TTSManager


class StageService:
    def __init__(self) -> None:
        self._tts = TTSManager()
        self._osc = OSCBridge()
        self._connections: List[Any] = []

        async def _broadcast(payload: Dict[str, Any]):
            stale: List[Any] = []
            for conn in list(self._connections):
                try:
                    await conn.send_json(payload)
                except Exception:
                    stale.append(conn)
            for s in stale:
                if s in self._connections:
                    self._connections.remove(s)

        self._director = StageDirector(tts=self._tts, osc=self._osc, progress_callback=_broadcast)

    # WebSocket connection management (FastAPI WebSocket compatible objectを想定)
    def add_ws(self, ws: Any) -> None:
        if ws not in self._connections:
            self._connections.append(ws)

    def remove_ws(self, ws: Any) -> None:
        if ws in self._connections:
            self._connections.remove(ws)

    async def play(self) -> Dict[str, Any]:
        log_manager.info("[StageService] Play requested")
        asyncio.create_task(self._director.play_timeline("data/timeline.json"))
        return {"status": "playing"}

    def health(self) -> Dict[str, Any]:
        return self._director.health_summary()

    async def stop(self) -> Dict[str, Any]:
        # 現状 Director に停止APIがなければ通知のみ
        log_manager.info("[StageService] Stop requested")
        return {"status": "stopped"}

    def get_timeline(self) -> Dict[str, Any]:
        timeline_path = "data/timeline.json"
        if not os.path.exists(timeline_path):
            script_parser = ScriptParser()
            dummy_script_path = "data/script.json"
            if not os.path.exists(dummy_script_path):
                dummy_script_content = {
                    "title": "Test Stage",
                    "scenes": [
                        {
                            "id": 1,
                            "character": "Shiroi",
                            "emotion": "joy",
                            "text": "こんにちは、瑞希。今日はシステムのデモを始めるね。",
                            "duration": 4.2,
                        },
                        {
                            "id": 2,
                            "character": "Mizuki",
                            "emotion": "calm",
                            "text": "よろしくねシロイ、準備はできてる？",
                            "duration": 3.5,
                        },
                    ],
                }
                os.makedirs(os.path.dirname(dummy_script_path), exist_ok=True)
                with open(dummy_script_path, "w", encoding="utf-8") as f:
                    json.dump(dummy_script_content, f, indent=2, ensure_ascii=False)

            script_data = script_parser.load_script(dummy_script_path)
            timeline = script_parser.parse(script_data)
            script_parser.export_timeline(timeline_path)
            log_manager.info("[StageService] Generated timeline from dummy script.")
            return timeline

        with open(timeline_path, "r", encoding="utf-8") as f:
            return json.load(f)
