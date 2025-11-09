# Real-time Dashboard (UI-v1.0) Documentation

## Overview
The Real-time Dashboard (UI-v1.0) provides a dynamic, real-time visualization of the Shiroi System Platform's (SSP) internal AI state and system metrics. It leverages WebSocket communication to display live updates of AI persona, cognitive processes, introspection logs, and system performance.

## Features
- **AI Persona State:** Displays current emotion, harmony score, and cognitive traits (assertiveness, empathy, curiosity, stability, creativity).
- **Cognitive Graph:** Visualizes cognitive traits using a Radar Chart.
- **Introspection Feed:** Shows a live stream of AI's internal thought processes and reasoning.
- **System Metrics:** Monitors CPU usage, memory usage, and other system performance indicators.

## Technical Stack
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, Framer Motion, Recharts, Zustand (for state management).
- **Backend:** FastAPI (for WebSocket endpoint).
- **Real-time Communication:** WebSocket.

## API Endpoint
- **WebSocket:** `ws://localhost:8000/ws/dashboard`
  - **Purpose:** Provides a continuous stream of real-time data updates for the dashboard.
  - **Data Format:** JSON messages, each containing a `type` field (`persona_state`, `introspection_log`, `system_metrics`) and associated data.

## Frontend Components
- `frontend/app/dashboard/page.tsx`: Main dashboard layout.
- `frontend/lib/wsClient.ts`: WebSocket client logic and Zustand store for state management.
- `frontend/components/dashboard/PersonaPanel.tsx`: Displays AI persona state.
- `frontend/components/dashboard/CognitiveGraph.tsx`: Visualizes cognitive traits.
- `frontend/components/dashboard/IntrospectionFeed.tsx`: Displays introspection logs.
- `frontend/components/dashboard/MetricsPanel.tsx`: Displays system performance metrics.

## Integration with SSP Modules (Future Work)
Currently, the backend WebSocket endpoint (`backend/api/dashboard_ws.py`) uses mock data for demonstration purposes. To fully integrate, the mock data functions (`get_mock_persona_state`, `get_mock_introspection_log`, `get_mock_system_metrics`) need to be replaced with calls to the actual SSP modules responsible for providing this data (e.g., `modules/persona_manager.py`, `modules/metacognition.py`, `modules/system_monitor.py`).

## KPIs (Key Performance Indicators)
- **WebSocket Connection Stability:** Target < 200ms for initial connection.
- **Dashboard Update Latency:** Target < 2% delay in displaying real-time data.
- **Data Consistency:** Target 90% consistency across RAG, Generator, Evaluator, Memory, and Emotion modules.

## Testing and Verification
- **Functional:** Manually verify all dashboard panels display and update correctly.
- **Performance:** Monitor FPS using the integrated `FPSMeter` component to ensure smooth UI (target 60 FPS).
- **Error Handling:** Test WebSocket disconnection and reconnection scenarios.
