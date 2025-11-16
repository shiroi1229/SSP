from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.causal_verifier import verify_causality

router = APIRouter(prefix="/causal", tags=["Causal"])


class VerifyRequest(BaseModel):
    event_id: str


@router.post("/verify")
def verify(request: VerifyRequest):
    result = verify_causality(request.event_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return result
