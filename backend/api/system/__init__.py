"""System-level routers (diagnostic, metrics, etc.)."""

from fastapi import APIRouter

from .diagnose import router as diagnose_router
from .metrics import router as metrics_router
from .rebalance import router as rebalance_router
from .singularity import router as singularity_router

router = APIRouter()
router.include_router(diagnose_router)
router.include_router(metrics_router)
router.include_router(rebalance_router)
router.include_router(singularity_router)
