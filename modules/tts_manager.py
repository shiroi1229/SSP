"""Emotion-aware TTS Manager that maps emotion vectors to Voicevox parameters."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Union

import requests
from playsound import playsound  # type: ignore


class TTSManager:
    def __init__(self, voicevox_url: str | None = None, output_dir: str | Path = "data/audio_outputs"):
        """Initialize TTSManager with Voicevox endpoint + output directory."""
        self.voicevox_url = voicevox_url or os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _adjust_params(self, emotion: Dict[str, Any]) -> Dict[str, float]:
        """Map emotion tags + intensity to Voicevox pitch/speed."""
        tag = (emotion.get("emotion_tags") or ["Neutral"])[0]
        intensity = float(emotion.get("intensity", 0.5))

        mapping = {
            "joy": {"pitch": 0.15, "speed": 1.15},
            "calm": {"pitch": -0.1, "speed": 0.9},
            "sad": {"pitch": -0.2, "speed": 0.85},
            "angry": {"pitch": 0.2, "speed": 1.2},
            "curious": {"pitch": 0.1, "speed": 1.05},
            "neutral": {"pitch": 0.0, "speed": 1.0},
        }

        base = mapping.get(tag.lower(), mapping["neutral"])
        final_pitch = base["pitch"] * intensity
        final_speed = 1 + (base["speed"] - 1) * intensity
        return {"pitchScale": final_pitch, "speedScale": final_speed}

    def _normalize_emotion_payload(self, emotion: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure downstream synthesis always receives dict payload."""
        if isinstance(emotion, dict):
            tags = emotion.get("emotion_tags") or []
            dominant = emotion.get("dominant_emotion")
            primary = (tags[0] if tags else dominant) or "Neutral"
            return {
                "emotion_tags": [primary if isinstance(primary, str) else "Neutral"],
                "intensity": float(emotion.get("intensity", 0.7)),
                "emotion_vector": emotion.get("emotion_vector"),
            }

        tag = (emotion or "neutral").strip().capitalize() or "Neutral"
        return {"emotion_tags": [tag], "intensity": 0.7, "emotion_vector": None}

    def synthesize(self, text: str, emotion_dict: Dict[str, Any], speaker_id: int = 1) -> str:
        """Generate TTS wav path using Voicevox."""
        if not text:
            return "Error: Input text is empty."

        params = self._adjust_params(emotion_dict)
        filename = f"tts_{speaker_id}_{hash(text + json.dumps(params, sort_keys=True))}.wav"
        output_path = self.output_dir / filename
        if output_path.exists():
            return str(output_path)

        try:
            query_response = requests.post(
                f"{self.voicevox_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10,
            )
            query_response.raise_for_status()
            query_data = query_response.json()
            query_data["speedScale"] = params["speedScale"]
            query_data["pitchScale"] = params["pitchScale"]
            query_data["volumeScale"] = 1.0
            query_data["intonationScale"] = 1.0
            query_data["prePhonemeLength"] = 0.1
            query_data["postPhonemeLength"] = 0.1

            synthesis_response = requests.post(
                f"{self.voicevox_url}/synthesis",
                params={"speaker": speaker_id},
                data=json.dumps(query_data),
                timeout=30,
            )
            synthesis_response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(synthesis_response.content)
            return str(output_path)
        except requests.RequestException as exc:
            return f"Error communicating with Voicevox: {exc}"
        except Exception as exc:  # pragma: no cover
            return f"An unexpected error occurred during TTS synthesis: {exc}"

    async def speak(self, text: str, emotion: Union[str, Dict[str, Any]] = "neutral", speaker_id: int = 1) -> Dict[str, Any]:
        """Synthesize + play audio, returning playback metadata."""
        emotion_dict = self._normalize_emotion_payload(emotion)
        audio_file_path = self.synthesize(text, emotion_dict, speaker_id)
        if audio_file_path.startswith("Error"):
            message = f"TTS Error: {audio_file_path}"
            print(message)
            return {"status": "error", "error": audio_file_path, "audio_path": None, "emotion": emotion_dict}

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, playsound, audio_file_path)
            return {"status": "played", "audio_path": audio_file_path, "emotion": emotion_dict}
        except Exception as exc:  # pragma: no cover - audio playback failure is environment-specific
            error_message = f"Error playing sound: {exc}"
            print(error_message)
            return {"status": "error", "error": error_message, "audio_path": audio_file_path, "emotion": emotion_dict}
