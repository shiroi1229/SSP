"""Awareness meta reporter that translates analysis into narratives."""

from __future__ import annotations

from typing import Dict, Any, List


class MetaReporter:
    """Generates human-readable meta reports from metrics."""

    def summarize(self, metrics: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
        summary_lines: List[str] = []
        highlights: List[str] = []
        self_coherence = metrics.get("self_coherence", {})
        cognitive_drift = metrics.get("cognitive_drift", {})
        emotional_stability = metrics.get("emotional_stability", {})

        if self_coherence:
            score = self_coherence["score"] * 100
            summary_lines.append(
                f"Self-Coherence is at {score:.0f}%, showing how consistently the system responds."
            )
        if cognitive_drift:
            drift = cognitive_drift["score"] * 100
            summary_lines.append(
                f"Cognitive Drift risk sits at {drift:.0f}%, so the awareness layer keeps watching for shifts."
            )
            if cognitive_drift["score"] > 0.5:
                highlights.append("Cognitive Drift demands attention; drifting patterns were observed.")
        if emotional_stability:
            stability = emotional_stability["score"] * 100
            summary_lines.append(
                f"Emotional Stability is {stability:.0f}%, indicating the valence curve stays near neutral."
            )
            if emotional_stability["score"] < 0.6:
                highlights.append("Emotional signals show volatility; deeper introspection is advised.")

        snapshot = observation.get("snapshot", {})
        detail = snapshot.get("awareness_summary")
        if detail:
            highlights.append(f"Recent awareness note: {detail}")

        return {
            "summary": summary_lines or ["No awareness signals were gathered."],
            "highlights": highlights,
            "raw_snapshot": observation.get("snapshot"),
        }
