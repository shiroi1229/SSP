# Shiroi-Gemini Roadmap Collaboration Protocol

This document outlines the protocol for collaborative editing and synchronization of the Shiroi System Platform (SSP) roadmap between Shiroi (GPT) and Gemini (this agent) via GitHub. The goal is to ensure both AI systems always have access to the latest development evolution information.

---

## 1. Data Flow Diagram (Textual Representation)

The roadmap data flows in a cyclical manner, ensuring continuous synchronization:

```
[Shiroi (GPT)] --(1. Edits JSON)--> [Gemini (Agent)] --(2. Commits & Pushes to GitHub)--> [GitHub Repository]
      ^                                                                                             |
      |                                                                                             |
      +---------------------------------------------------------------------------------------------+
      |                                                                                             |
      +--(4. Fetches & Updates Context)--------------------------------------------------------------+
      |                                                                                             |
      +--(3. auto_sync_monitor fetches from GitHub)--------------------------------------------------+
```

**Explanation:**
1.  **Shiroi (GPT) Edits JSON:** Shiroi, through its internal processes or direct interaction, proposes updates to the roadmap JSON files. These changes are then communicated to Gemini.
2.  **Gemini Commits & Pushes to GitHub:** Gemini, upon receiving updates or making its own, commits the changes to the `docs/roadmap/` directory in the shared GitHub repository and pushes them to the `main` branch.
3.  **`auto_sync_monitor` Fetches from GitHub:** A dedicated `auto_sync_monitor.py` module (running within Gemini's environment) periodically fetches the latest `system_roadmap_extended.json` from the GitHub repository.
4.  **`auto_sync_monitor` Updates Context:** If changes are detected, the monitor logs the differences, updates a local cache, saves a snapshot, and triggers an update to Shiroi's long-term context, ensuring Shiroi is aware of the latest roadmap.

---

## 2. JSON Structure Specification

The roadmap is defined in two primary JSON files:

*   `system_roadmap.json`: Contains confirmed, past, and current phases (v0.1 to v2.5).
*   `system_roadmap_extended.json`: Includes all phases, extending to future projections (v0.1 to v4.0).

Both files adhere to the following structure for each category (`backend`, `frontend`, `robustness`):

```json
{
  "backend": [
    {
      "version": "string",       // e.g., "v2.4"
      "codename": "string",      // e.g., "Context Evolution"
      "goal": "string",          // Short description of the phase's objective
      "status": "string",        // Status indicator (see below)
      "description": "string",   // Detailed description of the phase
      "time": "string",          // "past", "current", or "future"
      "impact_level": "number?"  // Optional: Numerical impact score (e.g., 1-5)
    }
  ],
  "frontend": [
    // ... similar RoadmapItem objects
  ],
  "robustness": [
    // ... similar RoadmapItem objects
  ]
}
```

**Key Definitions:**

*   `version`: Unique version identifier (e.g., "v2.4", "v3.0").
*   `codename`: A memorable name for the phase.
*   `goal`: A concise statement of what the phase aims to achieve.
*   `status`: Indicates the current state of the phase.
    *   `"✅"`: Completed.
    *   `"🔄"`: In Progress / Active Development.
    *   `"⚪"`: Planned / Future.
*   `description`: A more detailed explanation of the phase's features or objectives.
*   `time`: Categorizes the phase relative to the current development.
    *   `"past"`: Already completed.
    *   `"current"`: Currently in active development or recently completed.
    *   `"future"`: Planned for future development.
*   `impact_level`: (Optional) A numerical value representing the perceived impact or importance of the phase.

---

## 3. Update Protocol (Manual & Automated)

### 3.1. Manual Updates (Gemini Initiated)

When Gemini (or a human operator) updates the roadmap JSON files:

1.  **Edit Files:** Modify `system_roadmap.json` and/or `system_roadmap_extended.json` in the `docs/roadmap/` directory.
2.  **Commit Changes:** Stage and commit the changes to the local Git repository.
    *   Commit message should follow conventional commits (e.g., `docs(roadmap): update v2.5 status`).
3.  **Push to GitHub:** Push the committed changes to the `main` branch of the shared GitHub repository (`git push origin main`).

### 3.2. Automated Synchronization (Shiroi Initiated / Monitor Driven)

1.  **GitHub Update:** Any push to the `main` branch of the `SSP` repository (either manual or automated) makes the latest roadmap available.
2.  **`auto_sync_monitor` Fetch:** The `modules/auto_sync_monitor.py` script, scheduled to run every 10 minutes, fetches `system_roadmap_extended.json` from GitHub.
3.  **Difference Detection:** The monitor compares the fetched roadmap with its local cache (`data/system_roadmap_cache.json`).
4.  **Context Update:** If differences are found:
    *   The changes are logged to `logs/roadmap_sync.log`.
    *   A snapshot of the new roadmap is saved to `logs/context_evolution/`.
    *   Shiroi's long-term context is updated via `ContextManager.update_roadmap()`, making the new roadmap immediately accessible to Shiroi's internal reasoning processes.

---

## 4. Future Vision: Automated Pull Request (PR) Integration (v3.0+)

In future iterations (v3.0 and beyond), the collaboration protocol will evolve to include automated Pull Request (PR) integration:

*   **Shiroi-Proposed Changes:** Shiroi will be capable of generating proposed roadmap changes (e.g., new phases, status updates) as structured data.
*   **Automated PR Creation:** Gemini will automatically convert these proposed changes into a new Git branch and create a Pull Request against the `main` branch on GitHub.
*   **Review & Merge:** Human operators or other AI systems can then review the proposed changes, provide feedback, and merge the PR.
*   **Continuous Integration:** Upon merging, the `auto_sync_monitor` will detect the update, ensuring Shiroi's context is refreshed with its own approved proposals.

This automated PR workflow will enable a more robust, auditable, and scalable collaborative development process.
