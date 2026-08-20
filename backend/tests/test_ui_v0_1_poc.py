import pytest
from pathlib import Path

from tools import ui_v0_1_poc_runner as runner


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {"references": [], "messageId": "msg-1"}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP error")


class DummySession:
    def __init__(self):
        self.calls = []

    def post(self, url, json=None, timeout=None):
        self.calls.append(url)
        if "/api/chat" in url:
            return DummyResponse(json_data={"references": [1], "messageId": "msg-1"})
        return DummyResponse()


def test_run_cycle(monkeypatch, tmp_path):
    runner.LOG_PATH = tmp_path / "logs" / "ui_v0_1_poc.jsonl"
    session = DummySession()
    monkeypatch.setattr(runner, "requests", session)
    result = runner.run_cycle("http://127.0.0.1:8000", "Test")
    runner.log(result)
    assert result["status"] == 200
    assert result["references"] == 1
    assert runner.LOG_PATH.exists()
