from fastapi import APIRouter, Query

from modules.bias_detector import detect_bias

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])


@router.get("/bias")
def get_bias(limit: int = Query(200, ge=20, le=600), threshold: float = Query(0.6, ge=0.1, le=1.0)):
    return detect_bias(limit, threshold)
