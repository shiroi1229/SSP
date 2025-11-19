"""Singularity Core status endpoint."""

from fastapi import APIRouter

from backend.core.singularity_controller import SingularityController

router = APIRouter(prefix="/system", tags=["System"])
controller = SingularityController()


@router.get("/singularity")
def singularity_status():
    """Return aggregated truthfulness/consistency metrics for Singularity Core."""
    return controller.run_full_assessment()
