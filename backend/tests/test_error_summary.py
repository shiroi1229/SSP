import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.error_summary import summary as error_summary
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


def _populate_logs(session):
    now = datetime.utcnow()
    session.add_all([
        SessionLog(
            id="success",
            user_input="POST /api/chat",
            status_code=200,
            response_time_ms=1200,
            log_persist_failed=0,
            regeneration_attempts=0,
            regeneration_success=False,
            evaluation_score=5,
            error_tag=None,
            impact_level=None,
            created_at=now - timedelta(minutes=5),
        ),
        SessionLog(
            id="upstream",
            user_input="POST /api/chat",
            status_code=502,
            response_time_ms=2200,
            log_persist_failed=0,
            regeneration_attempts=0,
            regeneration_success=False,
            evaluation_score=3,
            error_tag="upstream_error",
            impact_level="critical",
            created_at=now - timedelta(minutes=10),
        ),
        SessionLog(
            id="validation",
            user_input="POST /api/chat/eval",
            status_code=400,
            response_time_ms=900,
            log_persist_failed=0,
            regeneration_attempts=0,
            regeneration_success=False,
            evaluation_score=2,
            error_tag="validation_error",
            impact_level="high",
            created_at=now - timedelta(minutes=15),
        ),
    ])
    session.commit()


def test_error_summary_counts(in_memory_session):
    _populate_logs(in_memory_session)
    payload = error_summary(db=in_memory_session)

    assert payload["total_sessions"] == 3
    assert payload["total_errors"] == 2
    assert payload["failure_rate"] == pytest.approx(2 / 3, rel=1e-3)
    tags = {entry["tag"] for entry in payload["errors_by_tag"]}
    assert "upstream_error" in tags
    assert "validation_error" in tags
    assert payload["impact_breakdown"][0]["impact_level"] in {"critical", "high"}
    assert payload["top_error_endpoints"][0]["endpoint"].startswith("POST")
