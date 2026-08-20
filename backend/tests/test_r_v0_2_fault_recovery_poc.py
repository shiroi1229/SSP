import pytest

from tools import r_v0_2_failure_injector as failure_injector
from tools import r_v0_2_supervisor_scenario_runner as scenario_runner


class DummySession:
    def __init__(self, status_sequence=None):
        self._status_sequence = status_sequence or [200]
        self._index = 0

    def request(self, method, url, **kwargs):
        status = self._status_sequence[self._index % len(self._status_sequence)]
        self._index += 1
        class Resp:
            def __init__(self, status):
                self.status_code = status
                self.text = f"{method} {url}"
        return Resp(status)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)


def test_failure_injector_sequence():
    session = DummySession([200, 500, 200])
    steps = failure_injector.POC_SCENARIOS["single-module"]
    results = failure_injector.inject_sequence(session, "http://127.0.0.1:8000", steps, pause=0)
    assert len(results) == len(steps)
    assert any(result["status"] == 500 for result in results)


def test_supervisor_scenario_summary():
    session = DummySession([200])
    summary = scenario_runner.run_scenario(
        session=session,
        base_url="http://127.0.0.1:8000",
        targets=["/api/system/health"],
        duration=0.0,
        interval=0.0,
    )
    assert "/api/system/health" in summary
    assert summary["/api/system/health"]["samples"] >= 1
