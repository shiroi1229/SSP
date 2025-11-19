"""Continuum state endpoint."""

from fastapi import APIRouter

from modules.continuum_core import ContinuumCore

router = APIRouter(prefix="/continuum", tags=["Continuum"])

core = ContinuumCore()


@router.get("/state")
def get_state():
    """Return the current continuum state snapshot."""
    return core.current_state()
