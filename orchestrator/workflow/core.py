# path: orchestrator/workflow/core.py
# version: v0.1
# purpose: Reusable workflow primitives for the orchestrator runtime

from __future__ import annotations

import os
from collections import namedtuple

from modules.alert_dispatcher import AlertDispatcher
from modules.auto_fix_executor import AutoFixExecutor
from modules.log_manager import log_manager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.context_manager import ContextManager
from orchestrator.context_validator import ContextValidator
from orchestrator.feedback_loop_integration import FeedbackLoop
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.learner import Learner
from orchestrator.meta_contract_engine import MetaContractEngine
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from qdrant_client import QdrantClient
from typing import List, Optional

WorkflowComponents = namedtuple(
    "WorkflowComponents",
    [
        "context_manager",
        "contract_registry",
        "context_validator",
        "policy_manager",
        "insight_monitor",
        "auto_fix_executor",
        "alert_dispatcher",
        "learner",
        "feedback_loop",
        "meta_contract_engine",
    ],
)


def initialize_components(user_input: str, history: Optional[List[dict]] = None) -> WorkflowComponents:
    context_manager = ContextManager(history_path="logs/context_history.json")
    contract_registry = ContractRegistry()
    context_validator = ContextValidator(contract_registry)
    policy_manager = RecoveryPolicyManager()
    insight_monitor = InsightMonitor(context_manager, policy_manager)
    auto_fix_executor = AutoFixExecutor()
    alert_dispatcher = AlertDispatcher()

    meta_contract_engine = MetaContractEngine()
    meta_contract_engine.load_contracts()

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    qdrant_client = QdrantClient(url=qdrant_url)
    learner = Learner(context_manager, qdrant_client)
    feedback_loop = FeedbackLoop(context_manager, contract_registry, insight_monitor, policy_manager)

    if history:
        context_manager.set("mid_term.chat_history", history, reason="Seed chat history from DB")
    context_manager.set("short_term.user_input", user_input, reason="Initial user input")
    context_manager.set("long_term.config.qdrant_url", qdrant_url, reason="Qdrant URL config")
    log_manager.info("Initial context and managers set up.")
    return WorkflowComponents(
        context_manager,
        contract_registry,
        context_validator,
        policy_manager,
        insight_monitor,
        auto_fix_executor,
        alert_dispatcher,
        learner,
        feedback_loop,
        meta_contract_engine,
    )
