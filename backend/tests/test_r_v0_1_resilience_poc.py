import time
from typing import Iterable, List

import pytest

from tools import r_v0_1_failure_injector as failure_injector
from tools import r_v0_1_supervisor_stress_runner as stress_runner


class FakeResponse:
    def __init__(self, status: int = 200, text: str = "OK"):
        self.status_code = status
        self.text = text


class FakeSession:
    def __init__(self, statuses: Iterable[int] = (200,)):
        self._statuses: List[int] = list(statuses)

    def request(self, method: str, url: str, **_: object) -> FakeResponse:
        status = self._statuses.pop(0) if self._statuses else 200
        return FakeResponse(status=status, text=f"{method} {url}")

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        return self.request("GET", url, **kwargs)


def test_failure_plan_injects_all_endpoints() -> None:
    plan = failure_injector.build_failure_plan()
    session = FakeSession(statuses=[200] * len(plan))
    results = failure_injector.inject_failures(session, "http://127.0.0.1:8000", plan, pause=0)
    assert len(results) == len(plan)
    assert all(result["status"] == 200 for result in results)


def test_supervisor_stress_returns_summary() -> None:
    session = FakeSession()
    report = stress_runner.run_supervisor_stress(
        session, "http://127.0.0.1:8000", duration=0.0, interval=0.0
    )
    summary = report["summary"]
    assert summary["samples"] >= 1
    assert summary["average_duration"] >= 0
    assert isinstance(summary["status_counts"], dict)
    assert summary["total_duration"] >= 0
