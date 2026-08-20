"""Middleware to log request metrics and response status."""

from __future__ import annotations

import time
import asyncio
from typing import Optional

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from backend.db.connection import SessionLocal, update_session_logs_table
from backend.db.models import SessionLog
from modules.log_manager import log_manager



def _classify_error_tag(status_code: int, exception: Optional[Exception]) -> Optional[str]:
    if exception is not None:
        if isinstance(exception, (asyncio.TimeoutError, TimeoutError)):
            return "timeout"
        return "upstream_error"
    if status_code >= 500:
        return "upstream_error"
    if status_code >= 400:
        return "validation_error"
    return None


def _determine_impact_level(status_code: int, error_tag: Optional[str]) -> str:
    if error_tag == "timeout" or status_code >= 500:
        return "critical"
    if status_code >= 400:
        return "high"
    return "normal"


def setup_metrics_middleware(app: FastAPI) -> None:
    update_session_logs_table()

    @app.middleware("http")
    async def metrics_logger(request: Request, call_next):
        start = time.perf_counter()
        success = True
        response = Response(status_code=500)
        exception: Optional[Exception] = None
        try:
            response = await call_next(request)
            success = response.status_code < 400
            return response
        except Exception as exc:  # pragma: no cover
            success = False
            response = Response(status_code=500)
            exception = exc
            log_manager.error("Request failed", exc_info=exc)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            if not request.url.path.startswith("/api/"):
                return

            regen_flag = request.headers.get("X-Regeneration", "").lower() in {"1", "true", "yes"} or \
                request.query_params.get("regeneration", "").lower() in {"1", "true", "yes"}
            status_code = getattr(response, "status_code", 500) or 500

            error_tag = _classify_error_tag(status_code, exception)
            impact_level = _determine_impact_level(status_code, error_tag)
            try:
                with SessionLocal() as session:
                    log_entry = SessionLog(
                        id=f"req-{int(time.time() * 1000)}",
                        user_input=f"{request.method} {request.url.path}",
                        final_output=str(status_code),
                        status_code=status_code,
                        response_time_ms=duration_ms,
                        log_persist_failed=0,
                        regeneration_attempts=1 if regen_flag else 0,
                        regeneration_success=bool(regen_flag and success),
                        error_tag=error_tag,
                        impact_level=impact_level,
                    )
                    session.merge(log_entry)
                    session.commit()
            except Exception as exc:  # pragma: no cover
                log_manager.error("Failed to persist metrics log", exc_info=exc)
