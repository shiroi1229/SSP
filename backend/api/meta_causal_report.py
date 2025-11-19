from fastapi import APIRouter, Query

from modules.meta_causal_report import build_meta_causal_report

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])


@router.get("/report")
def meta_causal_report(limit: int = Query(120, ge=20, le=300)):
    return build_meta_causal_report(limit=limit)
