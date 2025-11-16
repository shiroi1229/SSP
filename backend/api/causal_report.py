from fastapi import APIRouter, HTTPException, Query

from modules.causal_report import generate_report

router = APIRouter(prefix="/causal", tags=["Causal"])


@router.get("/report")
def causal_report(event_id: str | None = Query(default=None)):
    report = generate_report(event_id)
    if report.get("success"):
        return report
    raise HTTPException(status_code=404, detail=report.get("detail", "Report unavailable"))
