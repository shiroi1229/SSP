from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
from modules.tts_manager import TTSManager
from backend.api.tts import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _mock_synthesize_success(self, text, emotion, speaker_id):
    path = "data/audio_outputs/test.wav"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x00")
    return path, False, None


def _mock_synthesize_error(self, text, emotion, speaker_id):
    return "", True, "tts_timeout"


def test_tts_endpoint_success(monkeypatch):
    monkeypatch.setattr(TTSManager, "synthesize", _mock_synthesize_success)
    payload = {"text": "hello world", "speaker_id": 1}
    response = client.post("/api/tts", json=payload)
    assert response.status_code == 200
    assert response.json()["text"] == "hello world"
    assert response.json()["fallback_used"] is False


def test_tts_endpoint_failure(monkeypatch):
    monkeypatch.setattr(TTSManager, "synthesize", _mock_synthesize_error)
    payload = {"text": "hello error", "speaker_id": 1}
    response = client.post("/api/tts", json=payload)
    assert response.status_code == 503
    assert "tts_timeout" in response.json()["detail"]
