# SSP v2.5 - Impact Analyzer & Auto-Repair Engine Specification

## 1. Overview

This document outlines the architecture of the Impact Analyzer and Auto-Repair Engine, core components of the SSP v2.5 "Immunity and Healing" initiative. The primary goal is to evolve SSP from an AI that simply detects anomalies to one that can understand the scope of a failure and attempt to repair itself, creating a more resilient and robust intelligent system.

-   **Impact Analyzer**: A diagnostic tool that, upon anomaly detection, traces module dependencies to determine the potential blast radius of the failure.
-   **Auto-Repair Engine**: A response system that uses the report from the Impact Analyzer to apply a suitable recovery strategy.

## 2. Architecture

### 2.1. Impact Analyzer (`orchestrator/impact_analyzer.py`)

The Impact Analyzer is responsible for assessing the potential damage of a given anomaly.

#### Core Components:

1.  **Dependency Graph (`config/dependency_graph.yaml`)**: A YAML file that defines the static dependency relationships between all major SSP modules. This is the map the analyzer uses to trace impact.

2.  **Reverse Dependency Graph**: For efficient downstream tracing, the analyzer builds an in-memory reverse graph upon initialization. This allows it to quickly find which modules *depend on* a failing module.

3.  **Trace Function (`trace_impact`)**: A recursive function that starts from a `source_module` and traverses the reverse dependency graph to build a complete set of all potentially affected downstream modules.

#### Impact Score Calculation:

The impact score is a metric from 0.0 to 1.0 that quantifies the severity of the failure in the context of the entire system.

**Formula:**

```
Impact Score = (Number of Affected Modules) / (Total Number of Modules in Graph)
```

-   A score of **0.1** means 10% of the system is potentially compromised.
-   A score of **1.0** indicates a catastrophic failure affecting all modules.

#### Reporting:

The analyzer generates a JSON and Markdown report for each analysis, saved to `/logs/impact_reports/`. The report includes:
-   `source_module`: The origin of the anomaly.
-   `impact_score`: The calculated score.
-   `affected_modules_count`: The number of affected modules.
-   `affected_modules`: The list of all modules in the impact chain.

### 2.2. Auto-Repair Engine (`orchestrator/auto_repair_engine.py`)

The Auto-Repair Engine acts on the analyzer's report to execute a repair strategy.

#### Repair Strategies:

The engine currently supports two primary strategies, chosen based on the impact score:

1.  **`soft` Repair (Low-to-Medium Impact, e.g., Score < 0.6)**:
    -   **Action**: Rolls back the system's state to the last known stable snapshot.
    -   **Mechanism**: It retrieves the ID of the last stable snapshot from the `ContextManager` (e.g., `system.last_stable_snapshot_id`) and instructs the `ContextManager` to perform a rollback.
    -   **Goal**: To revert the system to a healthy state before the anomaly occurred, sacrificing the progress of the current cycle.

2.  **`rebuild` Repair (High Impact, e.g., Score >= 0.6)**:
    -   **Action**: Simulates a module rebuild by clearing all context associated with the affected modules.
    -   **Mechanism**: This is a more drastic measure. It instructs the `ContextManager` to purge any short-term and mid-term data related to the compromised modules. 
    -   **Constraint**: True dynamic reloading of Python modules is not yet implemented due to its complexity. The current `rebuild` is a state-clearing simulation, not a code reload.
    -   **Goal**: To flush out potentially corrupted state and force the system to re-initialize the affected parts on the next cycle.

#### Workflow:

1.  **Receive Report**: The engine is triggered by the Orchestrator, which passes the impact report.
2.  **Select Strategy**: It selects `soft` or `rebuild` based on the `impact_score`.
3.  **Execute**: It calls the appropriate internal method (`_execute_soft_repair` or `_execute_rebuild_repair`).
4.  **Log History**: It logs the action taken, the targets, and the outcome to the `ContextManager`'s history (`repair_log`).
5.  **Verify**: It triggers a `verify_after_repair` step, which currently logs a message indicating the orchestrator should re-run the failed task.

## 3. Constraints & System Integration

-   **Context is King**: All state modifications *must* go through the `ContextManager`. The repair engine does not hold or modify state directly; it only issues commands to the `ContextManager`.
-   **Thread Safety**: All access to shared context is assumed to be managed by the `ContextManager` through a locking mechanism to ensure thread safety.
-   **Statelessness**: The Analyzer and Repair Engine are designed to be stateless. They are initialized on-demand and derive all necessary information from the `ContextManager` and the static dependency graph.
-   **Integration Points**:
    1.  **Anomaly Detection**: The primary trigger point is after the `InsightMonitor` detects an anomaly in the main workflow.
    2.  **Critical Exception**: A global `try...except` block in the main orchestrator also triggers the repair mechanism as a last-resort recovery attempt.
    3.  **Success-Path Testing**: For continuous validation, a test run of the analyzer is performed on every successful cycle.

## 4. Future Work

-   **Dynamic Dependency Graph**: Evolve the static YAML graph into a dynamic one that can be updated by the AI as it learns about module interactions.
-   **Advanced Repair Strategies**: Implement more granular repair strategies, such as re-running a specific function with different parameters or dynamically reloading a module's configuration.
-   **Predictive Analysis**: Use historical impact reports to predict which modules are most likely to fail in certain contexts.
