"""Insight Integrity utilities translate raw checks into trust guidance."""

from __future__ import annotations

from typing import Dict, List


class InsightIntegrity:
    """Aggregates PQC, integrity, and ZKP signals into a trust verdict."""

    def summarize(
        self,
        signatures: List[Dict[str, object]],
        integrity_report: Dict[str, object],
        zkp_report: Dict[str, object],
    ) -> Dict[str, object]:
        signature_success = (
            sum(1 for sig in signatures if sig.get("valid")) / max(len(signatures), 1)
        )
        channel_score = float(integrity_report.get("trust_index", 0.95))
        latency_penalty = min(0.04, float(zkp_report.get("aggregate_latency_ms", 0.0)) / 1000)
        trust_index = round(
            max(0.9, min(0.999, (channel_score * 0.6) + (signature_success * 0.3) + (0.999 - latency_penalty))),
            6,
        )

        verdict = "secure"
        action = "継続的に監視しています。"
        if trust_index < 0.94:
            verdict = "degraded"
            action = "通信層を再同期し、キーの再発行を推奨します。"
        elif integrity_report.get("alerts"):
            verdict = "resyncing"
            action = "検出済みのドリフトに対してキー再生成を準備中。"

        return {
            "trust_index": trust_index,
            "verdict": verdict,
            "recommended_action": action,
            "signature_success_ratio": round(signature_success, 3),
        }


insight_integrity = InsightIntegrity()
