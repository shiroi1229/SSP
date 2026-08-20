from fastapi import APIRouter, Query

from modules.bias_history import compute_long_term_bias

router = APIRouter(prefix="/meta_causal", tags=["MetaCausal"])

@router.get("/bias/history")
def get_bias_history(limit: int = Query(200, ge=20, le=800)):
    return compute_long_term_bias(limit)
