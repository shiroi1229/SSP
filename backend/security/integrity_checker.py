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

        for entry in raw_channels:
            payload_json = json.dumps(entry["payload"], sort_keys=True, default=str)
            digest = self._hash(payload_json)
            channels.append(
                {
                    "name": entry["name"],
                    "hash": digest,
                    "status": entry["status"],
                    "drift": entry["drift"],
                    "last_verified": entry["last_verified"],
                    "statement": entry["statement"],
                }
            )
            alerts.extend([f"{entry['name']}: {msg}" for msg in entry.get("alerts", [])])

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
            "generated_at": now,
        }


integrity_checker = IntegrityChecker()
