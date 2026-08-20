from fastapi import APIRouter, Query

from modules.optimizer_history import read_optimizer_history

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])


@router.get("/optimizer/history")
def optimizer_history(limit: int = Query(40, ge=5, le=200)):
    entries = read_optimizer_history(limit)
    return {"entries": entries, "summary": _summarize(entries)}


def _summarize(entries):
    if not entries:
        return {"count": 0}
    latest = entries[-1]
    temps = []
    top_ps = []
    for entry in entries:
        params = entry.get("params") or {}
        if "temperature" in params:
            temps.append(float(params["temperature"]))
        if "top_p" in params:
            top_ps.append(float(params["top_p"]))
    return {
        "count": len(entries),
        "latest": latest,
        "averages": {
            "temperature": round(sum(temps) / len(temps), 3) if temps else None,
            "top_p": round(sum(top_ps) / len(top_ps), 3) if top_ps else None,
        },
    }
