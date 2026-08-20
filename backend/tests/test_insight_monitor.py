from orchestrator.insight_monitor import InsightMonitor


def _setup_graph(monkeypatch, nodes=None):
    nodes = nodes or [{"event_id": "e1"}]
    monkeypatch.setattr(
        "orchestrator.insight_monitor.causal_graph.build_graph",
        lambda: {"nodes": nodes, "edges": []},
    )


def _setup_failures(monkeypatch, success=False):
    def fake_verify(event_id):
        if success:
            return {"success": True, "missing_parents": []}
        return {"success": False, "missing_parents": ["missing-seed"]}

    monkeypatch.setattr("orchestrator.insight_monitor.verify_causality", fake_verify)


def _setup_rollback(monkeypatch, payload):
    class DummyRollback:
        def rollback(self, *_args, **_kwargs):
            return payload

    monkeypatch.setattr("orchestrator.insight_monitor.rollback_manager", DummyRollback())


def test_compute_causal_integrity_skips_auto_action(monkeypatch):
    monitor = InsightMonitor.__new__(InsightMonitor)
    _setup_graph(monkeypatch)
    _setup_failures(monkeypatch)
    monkeypatch.setattr("orchestrator.insight_monitor.ingest_from_history", lambda limit=50: {"success": True})
    _setup_rollback(monkeypatch, {"success": True})
    log_calls = []
    monkeypatch.setattr("orchestrator.insight_monitor.log_action", lambda *args, **kwargs: log_calls.append((args, kwargs)))
    monkeypatch.setattr(
        "orchestrator.insight_monitor.compute_action_stats",
        lambda limit=200: {"causal_auto_action": {"count": 8, "success": 2, "success_ratio": 0.25}},
    )
    monkeypatch.setattr("orchestrator.insight_monitor.should_execute", lambda *a, **k: False)

    result = monitor.compute_causal_integrity(sample_size=1)

    assert result["auto_action"]["skipped"] is True
    assert result["auto_action"]["stats"]["success_ratio"] == 0.25
    assert log_calls == []


def test_compute_causal_integrity_executes_with_success_flag(monkeypatch):
    monitor = InsightMonitor.__new__(InsightMonitor)
    _setup_graph(monkeypatch)
    _setup_failures(monkeypatch)
    ingest_result = {"success": True}
    rollback_result = {"success": False}
    monkeypatch.setattr("orchestrator.insight_monitor.ingest_from_history", lambda limit=50: ingest_result)
    _setup_rollback(monkeypatch, rollback_result)
    log_calls = []

    def fake_log(action, success=None):
        log_calls.append({"action": action, "success": success})

    monkeypatch.setattr("orchestrator.insight_monitor.log_action", fake_log)
    monkeypatch.setattr(
        "orchestrator.insight_monitor.compute_action_stats",
        lambda limit=200: {"causal_auto_action": {"count": 10, "success": 7, "success_ratio": 0.7}},
    )
    monkeypatch.setattr("orchestrator.insight_monitor.should_execute", lambda *a, **k: True)

    result = monitor.compute_causal_integrity(sample_size=1)

    assert result["auto_action"]["decision"] == "executed"
    assert result["auto_action"]["success"] is False
    assert result["auto_action"]["stats"]["success_ratio"] == 0.7
    assert log_calls[0]["success"] is False
