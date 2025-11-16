from fastapi import APIRouter, Query

from modules.causal_ingest import ingest_from_history
from modules.causal_graph import causal_graph

router = APIRouter(prefix="/causal", tags=["Causal"])


@router.post("/ingest")
def ingest_causal_events(limit: int = Query(200, ge=10, le=500)):
    return ingest_from_history(limit)


@router.get("/graph")
def get_causal_graph():
    return causal_graph.build_graph()
