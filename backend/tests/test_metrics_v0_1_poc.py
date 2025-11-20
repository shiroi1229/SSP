import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.metrics_v0_1 import summary, timeseries
from backend.db.models import SessionLog


def _session_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLog.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def in_memory_session():
    yield from _session_fixture()


def _populate_sample_logs(session):
    now = datetime.utcnow()
    sample_logs = [
        SessionLog(
            id="log-now",
            user_input="/api/chat",
            final_output="200",
            status_code=200,
            response_time_ms=1000,
            log_persist_failed=0,
            evaluation_score=5,
            regeneration_attempts=0,
            regeneration_success=False,
            created_at=now - timedelta(minutes=15),
        ),
        SessionLog(
            id="log-old",
            user_input="/api/chat",
            final_output="500",
            status_code=500,
            response_time_ms=2000,
            log_persist_failed=1,
            evaluation_score=4,
            regeneration_attempts=0,
            regeneration_success=False,
            created_at=now - timedelta(minutes=75),
        ),
        SessionLog(
            id="log-reg",
            user_input="/api/chat",
            final_output="200",
            status_code=200,
            response_time_ms=1500,
            log_persist_failed=0,
            evaluation_score=3,
            regeneration_attempts=1,
            regeneration_success=True,
            created_at=now - timedelta(minutes=30),
        ),
    ]

    session.add_all(sample_logs)
    session.commit()
    return now


def test_summary_aggregates_kpis(in_memory_session):
    _populate_sample_logs(in_memory_session)
    payload = summary(db=in_memory_session)

    assert payload["samples"] == 3
    assert payload["path_filter"] is None
    assert payload["hours"] == 24
    assert payload["avg_response_time_sec"] == pytest.approx(1.5)
    assert payload["success_rate"] == pytest.approx(0.667, rel=1e-3)
    assert payload["regeneration_success_rate"] == pytest.approx(1.0)
    assert payload["log_loss_rate"] == pytest.approx(1 / 3, rel=1e-3)
    assert payload["score_5_ratio"] == pytest.approx(1 / 3, rel=1e-3)


def test_timeseries_breaks_data_by_hour(in_memory_session):
    _populate_sample_logs(in_memory_session)
    result = timeseries(hours=2, db=in_memory_session)

    assert len(result["points"]) == 2
    older, recent = result["points"]
    assert older["samples"] == 1
    assert older["success_rate"] == 0
    assert recent["samples"] == 2
    assert recent["success_rate"] == 1
    assert recent["regeneration_success_rate"] == 1

