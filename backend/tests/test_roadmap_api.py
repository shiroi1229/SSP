import pytest
from fastapi import HTTPException

from backend.api import roadmap
from backend.db.models import RoadmapItem as DBRoadmapItem


class DummyQuery:
    def __init__(self, versions):
        self._rows = [(v,) for v in versions]

    def all(self):
        return list(self._rows)


class DummyDB:
    def __init__(self, versions):
        self._versions = versions

    def query(self, attr):
        assert attr == DBRoadmapItem.version
        return DummyQuery(self._versions)


def test_normalize_payload_fields_infers_defaults():
    payload = {
        "keyFeatures": "  - item A\n- item B  ",
        "dependencies": None,
        "owner": "",
    }
    normalized = roadmap._normalize_payload_fields(payload, fill_missing=True)
    assert normalized["keyFeatures"] == ["item A", "item B"]
    assert normalized["dependencies"] == []
    assert normalized["metrics"] == []
    assert normalized["owner"] is None
    assert normalized["documentationLink"] is None
    assert normalized["prLink"] is None


def test_validate_dependencies_accepts_existing_versions():
    db = DummyDB(["v1.0", "A-v0.1"])
    roadmap._validate_dependencies(["v1.0", "A-v0.1"], db)


def test_validate_dependencies_raises_on_missing_version():
    db = DummyDB(["v1.0"])
    with pytest.raises(HTTPException) as excinfo:
        roadmap._validate_dependencies(["v1.0", "A-v0.1"], db)
    assert excinfo.value.status_code == 400
    assert "Dependencies not found" in excinfo.value.detail
