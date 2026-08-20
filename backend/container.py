# path: backend/container.py
# version: 1.0
"""
This module provides a centralized container for managing and injecting dependencies (services, managers)
across the SSP application. It ensures that components are instantiated consistently
and can be easily replaced for testing purposes.
"""
import os
from functools import lru_cache
from qdrant_client import QdrantClient

from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.context_validator import ContextValidator
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.feedback_loop_integration import FeedbackLoop
from orchestrator.learner import Learner
from orchestrator.impact_analyzer import ImpactAnalyzer
from orchestrator.auto_repair_engine import AutoRepairEngine
from modules.alert_dispatcher import AlertDispatcher
from modules.auto_fix_executor import AutoFixExecutor
from modules.log_manager import log_manager

# Using lru_cache(maxsize=None) as a simple way to create singletons
# The function will be executed only once, and its result will be cached.

@lru_cache(maxsize=None)
def get_qdrant_client() -> QdrantClient:
    log_manager.info("Initializing QdrantClient...")
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))

@lru_cache(maxsize=None)
def get_context_manager() -> ContextManager:
    log_manager.info("Initializing ContextManager...")
    return ContextManager(history_path="logs/context_history.json")

@lru_cache(maxsize=None)
def get_contract_registry() -> ContractRegistry:
    log_manager.info("Initializing ContractRegistry...")
    return ContractRegistry()

@lru_cache(maxsize=None)
def get_recovery_policy_manager() -> RecoveryPolicyManager:
    log_manager.info("Initializing RecoveryPolicyManager...")
    return RecoveryPolicyManager()

@lru_cache(maxsize=None)
def get_insight_monitor() -> InsightMonitor:
    log_manager.info("Initializing InsightMonitor...")
    return InsightMonitor(get_context_manager(), get_recovery_policy_manager())

@lru_cache(maxsize=None)
def get_learner() -> Learner:
    log_manager.info("Initializing Learner...")
    return Learner(get_context_manager(), get_qdrant_client())

@lru_cache(maxsize=None)
def get_feedback_loop() -> FeedbackLoop:
    log_manager.info("Initializing FeedbackLoop...")
    return FeedbackLoop(
        get_context_manager(),
        get_contract_registry(),
        get_insight_monitor(),
        get_recovery_policy_manager()
    )

@lru_cache(maxsize=None)
def get_alert_dispatcher() -> AlertDispatcher:
    log_manager.info("Initializing AlertDispatcher...")
    return AlertDispatcher()

@lru_cache(maxsize=None)
def get_auto_fix_executor() -> AutoFixExecutor:
    log_manager.info("Initializing AutoFixExecutor...")
    return AutoFixExecutor()

@lru_cache(maxsize=None)
def get_context_validator() -> ContextValidator:
    log_manager.info("Initializing ContextValidator...")
    return ContextValidator(get_contract_registry())

@lru_cache(maxsize=None)
def get_impact_analyzer() -> ImpactAnalyzer:
    log_manager.info("Initializing ImpactAnalyzer...")
    return ImpactAnalyzer(get_context_manager(), get_contract_registry())

@lru_cache(maxsize=None)
def get_auto_repair_engine() -> AutoRepairEngine:
    log_manager.info("Initializing AutoRepairEngine...")
    return AutoRepairEngine(get_context_manager())

class AppContainer:
    """A central access point for all dependencies."""
    @property
    def qdrant_client(self) -> QdrantClient:
        return get_qdrant_client()

    @property
    def context_manager(self) -> ContextManager:
        return get_context_manager()

    @property
    def contract_registry(self) -> ContractRegistry:
        return get_contract_registry()

    @property
    def recovery_policy_manager(self) -> RecoveryPolicyManager:
        return get_recovery_policy_manager()

    @property
    def insight_monitor(self) -> InsightMonitor:
        return get_insight_monitor()

    @property
    def learner(self) -> Learner:
        return get_learner()

    @property
    def feedback_loop(self) -> FeedbackLoop:
        return get_feedback_loop()
    
    @property
    def alert_dispatcher(self) -> AlertDispatcher:
        return get_alert_dispatcher()

    @property
    def auto_fix_executor(self) -> AutoFixExecutor:
        return get_auto_fix_executor()

    @property
    def context_validator(self) -> ContextValidator:
        return get_context_validator()

    @property
    def impact_analyzer(self) -> ImpactAnalyzer:
        return get_impact_analyzer()

    @property
    def auto_repair_engine(self) -> AutoRepairEngine:
        return get_auto_repair_engine()

# Global container instance
container = AppContainer()
