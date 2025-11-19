"""Data access helpers for world_timeline_events (fantasy timeline)."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from sqlalchemy import text

from backend.db.connection import engine


BASE_SELECT = """
    SELECT
        id,
        title,
        description,
        era,
        faction,
        start_year,
        end_year,
        COALESCE(importance, 0.5) AS importance,
        COALESCE(tags, '[]'::jsonb) AS tags,
        COALESCE(metadata, '{}'::jsonb) AS metadata
    FROM world_timeline_events
"""

QUERY = text(
    BASE_SELECT
    + """
    WHERE (:era IS NULL OR era = :era)
      AND (:faction IS NULL OR faction = :faction)
    ORDER BY start_year ASC, importance DESC
    """
)

GET_ONE = text(BASE_SELECT + " WHERE id = :event_id")

INSERT_EVENT = text(
    """
    INSERT INTO world_timeline_events
        (title, description, era, faction, start_year, end_year, importance, tags, metadata)
    VALUES
        (:title, :description, :era, :faction, :start_year, :end_year, :importance, :tags, :metadata)
    RETURNING id
    """
)

UPDATE_EVENT = text(
    """
    UPDATE world_timeline_events
    SET
        title = :title,
        description = :description,
        era = :era,
        faction = :faction,
        start_year = :start_year,
        end_year = :end_year,
        importance = :importance,
        tags = :tags,
        metadata = :metadata
    WHERE id = :event_id
    RETURNING id
    """
)

DELETE_EVENT = text("DELETE FROM world_timeline_events WHERE id = :event_id")


def _format_row(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "era": row["era"],
        "faction": row["faction"],
        "start_year": row["start_year"],
        "end_year": row["end_year"],
        "importance": float(row["importance"] or 0.5),
        "tags": row["tags"],
        "metadata": row["metadata"],
    }


def _json_value(value, default):
    if value is None:
        return json.dumps(default)
    return json.dumps(value)


def fetch_world_timeline(era: Optional[str] = None, faction: Optional[str] = None) -> List[Dict[str, object]]:
    with engine.connect() as conn:
        result = conn.execute(QUERY, {"era": era, "faction": faction})
        rows = result.mappings().all()
    return [_format_row(row) for row in rows]


def fetch_world_event(event_id: int) -> Dict[str, object] | None:
    with engine.connect() as conn:
        row = conn.execute(GET_ONE, {"event_id": event_id}).mappings().first()
    return _format_row(row) if row else None


def create_world_event(payload: Dict[str, object]) -> Dict[str, object]:
    params = {
        "title": payload["title"],
        "description": payload.get("description"),
        "era": payload.get("era"),
        "faction": payload.get("faction"),
        "start_year": payload["start_year"],
        "end_year": payload.get("end_year"),
        "importance": payload.get("importance", 0.5),
        "tags": _json_value(payload.get("tags"), []),
        "metadata": _json_value(payload.get("metadata"), {}),
    }
    with engine.begin() as conn:
        result = conn.execute(INSERT_EVENT, params)
        event_id = result.scalar_one()
    return fetch_world_event(event_id) or {}


def update_world_event(event_id: int, payload: Dict[str, object]) -> Dict[str, object] | None:
    params = {
        "event_id": event_id,
        "title": payload["title"],
        "description": payload.get("description"),
        "era": payload.get("era"),
        "faction": payload.get("faction"),
        "start_year": payload["start_year"],
        "end_year": payload.get("end_year"),
        "importance": payload.get("importance", 0.5),
        "tags": _json_value(payload.get("tags"), []),
        "metadata": _json_value(payload.get("metadata"), {}),
    }
    with engine.begin() as conn:
        result = conn.execute(UPDATE_EVENT, params)
        if result.scalar_one_or_none() is None:
            return None
    return fetch_world_event(event_id)


def delete_world_event(event_id: int) -> bool:
    with engine.begin() as conn:
        result = conn.execute(DELETE_EVENT, {"event_id": event_id})
    return result.rowcount > 0
