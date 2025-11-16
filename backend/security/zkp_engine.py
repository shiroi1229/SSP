"""Zero-Knowledge proof simulator used by the Quantum Safety Protocol."""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass
class ProofResult:
    claim: str
    channel: str
    transcript_root: str
    latency_ms: float
    valid: bool


class ZKPEngine:
    """Provides lightweight ZKP generation/verification for monitoring."""

    def _prove(self, channel: Dict[str, object]) -> ProofResult:
        start = time.perf_counter()
        statement = f"{channel['name']}::{channel['status']}::{channel['drift']}"
        transcript_root = hashlib.sha3_256(statement.encode()).hexdigest()
        latency = (time.perf_counter() - start) * 1000 + 32.0
        valid = channel["status"] != "rekeying"
        claim = f"{channel['name'].upper()}-{transcript_root[:6]}"
        return ProofResult(
            claim=claim,
            channel=channel["statement"],
            transcript_root=transcript_root,
            latency_ms=round(latency, 3),
            valid=valid,
        )

    def run_proofs(self, channels: List[Dict[str, object]]) -> Dict[str, object]:
        proofs = [self._prove(channel) for channel in channels]
        aggregate_latency = round(sum(proof.latency_ms for proof in proofs), 2)
        failing = any(not proof.valid for proof in proofs)
        network_state = "synchronized" if not failing else "verifying"
        return {
            "proofs": [asdict(proof) for proof in proofs],
            "aggregate_latency_ms": aggregate_latency,
            "network_state": network_state,
        }


zkp_engine = ZKPEngine()
