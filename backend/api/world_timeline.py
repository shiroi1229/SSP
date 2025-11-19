from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.world_timeline import (
    fetch_world_timeline,
    fetch_world_event,
    create_world_event,
    update_world_event,
    delete_world_event,
)

router = APIRouter(prefix="/world", tags=["World"])


class TimelineEventPayload(BaseModel):
    title: str
    description: str | None = None
    era: str | None = None
    faction: str | None = None
    start_year: int
    end_year: int | None = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] | None = None
    metadata: dict | None = None


def _collect_groups(events):
    seen = []
    for event in events:
        era = event.get("era") or "Unclassified"
        if era not in seen:
            seen.append(era)
    return [{"id": era, "content": era} for era in seen]


@router.get("/timeline")
def get_world_timeline(era: str | None = Query(default=None), faction: str | None = Query(default=None)):
    events = fetch_world_timeline(era=era, faction=faction)
    return {
        "events": events,
        "groups": _collect_groups(events),
        "query": {"era": era, "faction": faction},
        "count": len(events),
    }


@router.post("/timeline", status_code=201)
def create_timeline_event(payload: TimelineEventPayload):
    event = create_world_event(payload.model_dump())
    return event


@router.put("/timeline/{event_id}")
def update_timeline_event(event_id: int, payload: TimelineEventPayload):
    existing = fetch_world_event(event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    updated = update_world_event(event_id, payload.model_dump())
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update event")
    return updated


@router.delete("/timeline/{event_id}", status_code=204)
def delete_timeline_event(event_id: int):
    success = delete_world_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True}
