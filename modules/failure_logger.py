"""Failure logging and Insight notification helpers."""

from __future__ import annotations

from typing import Any, Dict

from modules.alert_dispatcher import AlertDispatcher
from modules.log_manager import log_manager


class FailureLogger:
    """Centralized failure logging with alert dispatch support."""

    def __init__(self) -> None:
        self.dispatcher = AlertDispatcher()

    def log_failure(self, error: Exception, context: str | None = None) -> None:
        message = f"Failure detected: {context or 'no context'}"
        log_manager.error(message, exc_info=True)
        self.dispatcher.dispatch_alert(f"{message} - {error}", severity="critical")

    def log_info(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        log_manager.info(message, extra=extra)


failure_logger = FailureLogger()
