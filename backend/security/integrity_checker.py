"""Integrity checking utilities for the Quantum Safety Protocol."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List

from backend.security.data_sources import gather_channel_metrics


class IntegrityChecker:
    """Computes integrity scores based on real log/config signals."""

    def __init__(self) -> None:
        self.sequence = 0

    def _hash(self, payload: str) -> str:
        return hashlib.sha3_384(payload.encode()).hexdigest()

    def inspect_channels(self) -> Dict[str, object]:
        self.sequence += 1
        now = datetime.now(timezone.utc).isoformat()
        raw_channels = gather_channel_metrics()
        channels: List[Dict[str, object]] = []
        alerts: List[str] = []
        summary_counts = {"verified": 0, "resyncing": 0, "rekeying": 0}
        max_drift = 0.0
        recommendations: List[Dict[str, str]] = []

        for entry in raw_channels:
            payload_json = json.dumps(entry["payload"], sort_keys=True, default=str)
            digest = self._hash(payload_json)
            severity = self._severity(entry["status"], entry["drift"])
            summary_counts[entry["status"]] = summary_counts.get(entry["status"], 0) + 1
            max_drift = max(max_drift, float(entry["drift"]))
            channels.append(
                {
                    "name": entry["name"],
                    "hash": digest,
                    "status": entry["status"],
                    "severity": severity,
                    "drift": entry["drift"],
                    "last_verified": entry["last_verified"],
                    "statement": entry["statement"],
                }
            )
            alerts.extend([f"{entry['name']}: {msg}" for msg in entry.get("alerts", [])])
            recommendation = self._recommendation_for(entry, severity)
            if recommendation:
                recommendations.append(recommendation)

        aggregate_payload = "".join(ch["hash"] for ch in channels)
        aggregate_hash = hashlib.sha3_512(aggregate_payload.encode()).hexdigest()
        drift_penalty = sum(max(0.0, ch["drift"] - 0.2) for ch in channels) / max(len(channels), 1)
        trust_index = round(max(0.90, 0.999 - drift_penalty), 6)

        return {
            "sequence": self.sequence,
            "channels": channels,
            "aggregate_hash": aggregate_hash,
            "trust_index": trust_index,
            "alerts": alerts,
            "summary": {
                "counts": summary_counts,
                "max_drift": round(max_drift, 3),
                "recommendations": len(recommendations),
                "generated_at": now,
            },
            "recommendations": recommendations,
            "generated_at": now,
        }

    def _severity(self, status: str, drift: float) -> str:
        if status == "rekeying" or drift >= 0.75:
            return "high"
        if status == "resyncing" or drift >= 0.4:
            return "medium"
        return "low"

    def _recommendation_for(self, entry: Dict[str, object], severity: str) -> Dict[str, str] | None:
        status = entry["status"]
        if severity == "low":
            return None
        if status == "rekeying":
            action = "Rotate PQC key and verify signatures."
        elif status == "resyncing":
            action = "Resync channel payloads and confirm drift stabilizes."
        else:
            action = "Investigate drift exceeding safe threshold."
        return {
            "channel": entry["name"],
            "action": action,
            "reason": entry.get("statement", ""),
        }


integrity_checker = IntegrityChecker()
