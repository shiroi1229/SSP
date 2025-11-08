# path: modules/emotion_engine.py
# version: v1
# Emotion Engine: シロイの返答テキストから感情タグを推定するモジュール。
# 使用モデル: GPT-5 / LM Studio / ローカルLoRA分類器（任意）

import requests
import json
import os
from typing import Dict, Any, List

class EmotionEngine:
    def __init__(self, llm_url: str | None = None):
        """
        Initializes the EmotionEngine.
        The LLM URL is determined by parameter, environment variable, or a default.
        """
        # This logic is similar to modules/llm.py, ensuring consistency
        config_path = "./config/model_params.json"
        default_url = "http://127.0.0.1:1234/v1"
        
        loaded_url = None
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    loaded_url = config.get("llm_url")
            except (json.JSONDecodeError, IOError):
                pass
        
        self.llm_url = llm_url or loaded_url or os.getenv("LOCAL_LLM_API_URL", default_url)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts the first valid JSON object from a string."""
        match = requests.utils.extract_json_from_content(text)
        if match:
            return json.loads(match)
        raise ValueError("No valid JSON found in the LLM response.")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the input text to estimate emotion tags and intensity.
        """
        prompt = f"""
        以下のテキストの主な感情を6種類（Joy, Calm, Sad, Angry, Curious, Neutral）の中から
        最大2つ選び、0.0〜1.0の強度をJSONで出力してください。
        出力はJSONオブジェクトのみとし、他のテキストは含めないでください。
        
        出力例:
        {{"emotion_tags": ["Joy","Curious"], "intensity": 0.73}}
        ---
        テキスト: {text}
        """

        payload = {
            "model": os.getenv("SSP_LOCAL_LLM_MODEL_NAME", "meta-llama-3-8b-instruct"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200,
            "response_format": {"type": "json_object"}, # Enforce JSON output
        }

        try:
            res = requests.post(f"{self.llm_url}/chat/completions", json=payload, timeout=20)
            res.raise_for_status()
            data = res.json()
            raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # The response content itself should be the JSON object
            result = json.loads(raw_content)

        except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            result = {"emotion_tags": ["Neutral"], "intensity": 0.0, "error": str(e)}

        return result
