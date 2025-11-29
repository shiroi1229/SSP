# Orchestration Evaluation - 2025-11-21

## Overview
SSP orchestrator v3 integrates layered context management, contract governance, anomaly detection, and recovery policies to run closed-loop cycles. Core components are initialized together (context manager, policy manager, insight monitor, learner, meta-contract engine) and seeded with user input before executing the feedback loop and post-loop learning hooks.

## Strengths
- **Layered context with snapshots/rollback.** The ContextManager persists short-, mid-, and long-term layers and supports snapshotting and rollback to restore stable states during orchestration faults.【F:orchestrator/context_manager.py†L20-L150】
- **Feedback loop resilience primitives.** Each loop run captures a snapshot, executes RAG→generation→evaluation, and uses policy-driven anomaly handling with bounded retries, enabling controlled recovery and state consistency across iterations.【F:orchestrator/feedback_loop_integration.py†L52-L129】
- **Predictive anomaly surfacing.** InsightMonitor combines real-time anomaly checks with a predictive analyzer that can trigger preemptive repair actions when risk surpasses a threshold, keeping signals in context for downstream policy decisions.【F:orchestrator/insight_monitor.py†L101-L184】

## Issues & Risks
1. **Snapshot trigger call breaks the main cycle.** `run_context_evolution_cycle` still calls `insight_monitor.trigger_snapshot`, but the InsightMonitor no longer exposes that method (even commented out elsewhere), so the orchestrator will raise an AttributeError before the feedback loop starts.【F:orchestrator/main.py†L324-L348】【F:orchestrator/feedback_loop_integration.py†L59-L60】
2. **Unbounded contract rewrites.** Before every cycle, the MetaContractEngine iterates over all contracts and applies suggested rewrites automatically without gating or validation, risking unintended contract drift across runs.【F:orchestrator/main.py†L324-L335】
3. **Test-only impact analysis runs in production path.** `_run_test_impact_analysis` executes on successful cycles by default, invoking mock impact tracing and auto-repair behaviors that can mutate context or logs even when no test mode is requested.【F:orchestrator/main.py†L278-L360】
4. **Predictive scheduler unused.** The predictive scheduler is imported but never started, so scheduled proactive policies never execute, leaving the orchestrator reliant on inline anomaly checks only.【F:orchestrator/main.py†L29-L35】

## Recommendations
- Reintroduce or replace the snapshot trigger with ContextManager-based snapshotting to unblock `run_context_evolution_cycle`, and add a regression test to prevent missing-method calls.
- Gate MetaContractEngine auto-rewrites behind configuration (e.g., `ENABLE_CONTRACT_REWRITE`) and validate diffs before applying to preserve contract stability.
- Wrap `_run_test_impact_analysis` behind a debug flag so production cycles skip mock repairs while retaining observability for test runs.
- Wire `start_predictive_scheduler` into the orchestrator startup (or remove the import) to ensure scheduled predictive policies run as designed.
