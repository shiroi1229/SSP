"""Continuum streaming endpoint."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from modules.continuum_core import ContinuumCore

router = APIRouter(prefix="/continuum", tags=["Continuum"])

core = ContinuumCore()


async def stream_generator():
    while True:
        snapshot = {"event": "continuum", "data": core.stream_state()}
        payload = "data: " + json.dumps(snapshot, ensure_ascii=False) + "\n\n"
        yield payload.encode("utf-8")
        await asyncio.sleep(3)


@router.get("/stream")
def continuum_stream():
    return StreamingResponse(stream_generator(), media_type="text/event-stream")
