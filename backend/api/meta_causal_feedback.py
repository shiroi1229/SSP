from fastapi import APIRouter, HTTPException, Query

from modules.causal_graph import causal_graph
from modules.meta_causal_feedback import run_feedback

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])

@router.get("/feedback")
def get_meta_causal_feedback():
    graph = causal_graph.build_graph()
    nodes = graph.get("nodes", [])
    latest = nodes[-6:]
    loops = []
    for node in latest:
        loops.append(
            {
                "event_id": node.get("event_id"),
                "description": node.get("description") or node.get("type"),
                "timestamp": node.get("timestamp"),
                "confidence": node.get("confidence"),
                "emotion": node.get("emotion_contribution", {}),
                "knowledge": node.get("knowledge_sources", []),
                "context": node.get("context_features", {}),
                "status": "improved" if node.get("confidence", 0) >= 0.7 else "review",
                "steps": [
                    {"label": "Input", "detail": node.get("metadata", {}).get("reason", "")},
                    {"label": "Evaluate", "detail": f"Parents: {', '.join(node.get('parents', [])) or 'None'}"},
                    {"label": "BiasDetect", "detail": ", ".join(node.get("emotion_contribution", {}).keys()) or "balanced"},
                    {"label": "Regenerate", "detail": node.get("description") or node.get("type")},
                ],
            }
        )
    return {"loops": loops[::-1]}

@router.post("/feedback/run")
def run_meta_feedback(limit: int = Query(200, ge=20, le=600), threshold: float = Query(0.6, ge=0.1, le=1.0)):
    from backend import main as backend_main

    context_manager = getattr(backend_main, "global_context_manager", None)
    result = run_feedback(context_manager, limit, threshold)
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("detail", "Feedback run failed"))
    return result
