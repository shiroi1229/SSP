# path: modules/tts_manager.py
# version: v1
# Emotion-aware TTS Manager
# Emotion Engineの出力を基にVoicevoxまたはCoeiroinkで音声を生成する。

import requests
import json
import os
from pathlib import Path
from typing import Dict, Any
import asyncio
from playsound import playsound # Import playsound

class TTSManager:
    def __init__(self, voicevox_url: str | None = None, output_dir: str | Path = "data/audio_outputs"):
        """
        Initializes the TTSManager.
        """
        self.voicevox_url = voicevox_url or os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _adjust_params(self, emotion: Dict[str, Any]) -> Dict[str, float]:
        """
        Maps emotion data to Voicevox synthesis parameters.
        """
        # Use the first tag as the primary emotion
        tag = emotion.get("emotion_tags", ["Neutral"])[0]
        intensity = emotion.get("intensity", 0.5)

        # Parameter mapping based on emotion
        mapping = {
            "joy": {"pitch": 0.15, "speed": 1.15},
            "calm": {"pitch": -0.1, "speed": 0.9},
            "sad": {"pitch": -0.2, "speed": 0.85},
            "angry": {"pitch": 0.2, "speed": 1.2},
            "curious": {"pitch": 0.1, "speed": 1.05},
            "neutral": {"pitch": 0.0, "speed": 1.0},
        }
        
        base = mapping.get(tag.lower(), mapping["neutral"]) # Convert tag to lowercase for matching
        
        # Apply intensity to the deviation from neutral
        # For pitch, intensity scales the deviation from 0
        # For speed, intensity scales the deviation from 1
        final_pitch = base["pitch"] * intensity
        final_speed = 1 + (base["speed"] - 1) * intensity

        return {
            "pitchScale": final_pitch,
            "speedScale": final_speed,
        }

    def synthesize(self, text: str, emotion_dict: Dict[str, Any], speaker_id: int = 1) -> str:
        """
        Generates speech with emotional parameters and returns the file path.
        """
        if not text:
            return "Error: Input text is empty."

        params = self._adjust_params(emotion_dict)
        
        # Create a unique filename based on text and params to allow caching
        filename = f"tts_{speaker_id}_{hash(text + json.dumps(params))}.wav"
        output_path = self.output_dir / filename

        # If file already exists, return path directly
        if output_path.exists():
            return str(output_path)

        try:
            # 1. Get audio query
            query_response = requests.post(
                f"{self.voicevox_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10,
            )
            query_response.raise_for_status()
            query_data = query_response.json()

            # 2. Apply emotional parameters
            query_data["speedScale"] = params["speedScale"]
            query_data["pitchScale"] = params["pitchScale"]
            query_data["volumeScale"] = 1.0
            query_data["intonationScale"] = 1.0
            query_data["prePhonemeLength"] = 0.1
            query_data["postPhonemeLength"] = 0.1

            # 3. Synthesize audio
            synthesis_response = requests.post(
                f"{self.voicevox_url}/synthesis",
                params={"speaker": speaker_id},
                data=json.dumps(query_data),
                timeout=30,
            )
            synthesis_response.raise_for_status()

            # 4. Save audio file
            with open(output_path, "wb") as f:
                f.write(synthesis_response.content)

            return str(output_path)
        except requests.RequestException as e:
            return f"Error communicating with Voicevox: {e}"
        except Exception as e:
            return f"An unexpected error occurred during TTS synthesis: {e}"

    async def speak(self, text: str, emotion: str = "neutral", speaker_id: int = 1):
        """
        Synthesizes and plays speech with a given emotion.
        Emotion is a string (e.g., "joy", "calm").
        """
        # Convert string emotion to dictionary format for synthesize method
        emotion_dict = {"emotion_tags": [emotion.capitalize()], "intensity": 0.7} # Default intensity
        
        audio_file_path = self.synthesize(text, emotion_dict, speaker_id)
        if audio_file_path.startswith("Error"):
            print(f"TTS Error: {audio_file_path}")
            return

        loop = asyncio.get_running_loop()
        try:
            # Run the blocking playsound function in a separate thread
            await loop.run_in_executor(None, playsound, audio_file_path)
        except Exception as e:
            print(f"Error playing sound: {e}")

