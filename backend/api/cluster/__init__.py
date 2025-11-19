"""Cluster API collection for R-v0.5."""

from __future__ import annotations

from fastapi import APIRouter

from .health import router as health_router
from .recover import router as recover_router

router = APIRouter()
router.include_router(health_router)
router.include_router(recover_router)
