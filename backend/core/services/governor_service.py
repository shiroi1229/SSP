# path: backend/core/services/governor_service.py
# version: v0.1
# purpose: Orchestrate analyzer/policy/patcher pipeline for autonomous code fixes

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict

from backend.modules.auto_patcher import apply_patch
from backend.modules.code_introspector import analyze_code_for_error
from backend.modules.governor_core import (
    CodeAnalysisResult,
    GovernorDirective,
    PatchSuggestion,
    evaluate_policy,
)


class PatchExecutionResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    backup: Optional[str] = None
    build_test_pass: Optional[bool] = None
    error: Optional[str] = None
    rolled_back: Optional[bool] = None


class GovernorRunResult(BaseModel):
    analysis: CodeAnalysisResult
    directive: GovernorDirective
    patch_result: Optional[PatchExecutionResult] = None


class GovernorService:
    """High-level governor pipeline that keeps modules decoupled."""

    def __init__(
        self,
        *,
        analyzer: Callable[[Dict[str, Any], str], Dict[str, Any]] = analyze_code_for_error,
        patcher: Callable[[str, str, str, str], Dict[str, Any]] = apply_patch,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._analyzer = analyzer
        self._patcher = patcher
        self._logger = logger or logging.getLogger("governor.service")

    def run(
        self,
        *,
        error_info: Dict[str, Any],
        file_path: str,
        confidence_threshold: float = 0.8,
    ) -> GovernorRunResult:
        self._logger.info("Evaluating governor pipeline for %s", file_path)
        raw_analysis = self._analyzer(error_info, file_path)
        analysis = CodeAnalysisResult.model_validate(raw_analysis)
        directive = evaluate_policy(
            analysis,
            high_conf_threshold=confidence_threshold,
            low_conf_note="Manual confirmation recommended before applying fix.",
        )

        patch_result: Optional[PatchExecutionResult] = None
        if directive.action == "auto_patch" and isinstance(directive.suggestion, PatchSuggestion):
            patch_status = self._patcher(
                file_path,
                directive.suggestion.instruction,
                directive.suggestion.old_code,
                directive.suggestion.new_code,
            )
            patch_result = PatchExecutionResult.model_validate(patch_status)

        outcome = GovernorRunResult(analysis=analysis, directive=directive, patch_result=patch_result)
        self._logger.info(
            "Governor directive=%s confidence=%.2f patch=%s",
            directive.action,
            directive.confidence,
            patch_result.status if patch_result else "n/a",
        )
        return outcome
