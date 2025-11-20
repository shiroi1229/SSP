import json

import pytest

from tools import r_v0_3_diagnostic_poc_runner as poc


class DummySession:
    def __init__(self):
        self.calls = 0

    class DummyResponse:
        def __init__(self):
            self.status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"summary": {"findings": []}, "alert": {}, "insight": {}}

    def get(self, url, timeout):
        self.calls += 1
        return self.DummyResponse()


def test_append_log_entries_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(poc, "LOG_PATH", tmp_path / "feedback.log")
    count = poc.append_log_entries(["entry one", "entry two"])
    assert count == 2
    assert (tmp_path / "feedback.log").exists()
    lines = (tmp_path / "feedback.log").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_call_diagnostic_direct_structure():
    payload = poc.call_diagnostic_stack("", None, mode="direct")
    assert "summary" in payload
    assert "alert" in payload
    assert "insight" in payload


def test_run_scenario_records(monkeypatch, tmp_path):
    monkeypatch.setattr(poc, "LOG_PATH", tmp_path / "feedback.log")
    monkeypatch.setattr(poc, "POC_LOG", tmp_path / "r_v0_3_poc.jsonl")
    summary = poc.run_scenario("", "baseline", None, "direct", pause=0.0)
    assert summary["scenario"] == "baseline"
    assert len(summary["steps"]) >= 2
    assert "total_findings" in summary
    assert summary["steps"][0]["type"] == "inject"
    assert summary["steps"][-1]["type"] == "diagnose"


def test_run_scenario_http(monkeypatch):
    dummy = DummySession()
    summary = poc.run_scenario("http://127.0.0.1:8000", "baseline", dummy, "http", pause=0.0)
    assert dummy.calls >= 1
    assert summary["steps"][-1]["type"] == "diagnose"
