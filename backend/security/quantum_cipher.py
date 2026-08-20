"""Quantum-safe signing utilities for the Quantum Safety Protocol (R-v0.6)."""

from __future__ import annotations

import hashlib
import secrets
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Deque, Dict, List


@dataclass
class PQCKey:
    key_id: str
    algorithm: str
    public_material: str
    private_material: str
    created_at: float


@dataclass
class SignatureRecord:
    message_id: str
    channel: str
    algorithm: str
    key_id: str
    digest: str
    salt: str
    signature: str
    issued_at: float
    latency_ms: float
    valid: bool


class QuantumCipher:
    """Simulates PQC signature workflows that protect internal cluster traffic."""

    SUPPORTED_ALGOS = ("CRYSTALS-Dilithium", "CRYSTALS-Kyber", "SPHINCS+")

    def __init__(self) -> None:
        self.active_key: PQCKey = self._generate_key()
        self.keyring: Dict[str, PQCKey] = {self.active_key.key_id: self.active_key}
        self.history: Deque[SignatureRecord] = deque(maxlen=64)

    def _generate_key(self) -> PQCKey:
        algorithm = secrets.choice(self.SUPPORTED_ALGOS)
        private_material = secrets.token_hex(64)
        public_material = hashlib.sha3_256(private_material.encode()).hexdigest()
        key_id = f"QC-{secrets.token_hex(4)}".upper()
        return PQCKey(
            key_id=key_id,
            algorithm=algorithm,
            public_material=public_material,
            private_material=private_material,
            created_at=time.time(),
        )

    def rotate_key(self) -> Dict[str, str]:
        """Rotate the active PQC key to simulate proactive defense."""
        new_key = self._generate_key()
        self.active_key = new_key
        self.keyring[new_key.key_id] = new_key
        # Keep the keyring compact to avoid unbounded growth.
        if len(self.keyring) > 8:
            oldest_key_id = next(iter(self.keyring))
            if oldest_key_id != new_key.key_id:
                self.keyring.pop(oldest_key_id)
        return self.describe_active_key()

    def sign_channel_digest(self, channel: str, digest_payload: str) -> Dict[str, object]:
        """Sign the provided digest and return a structured record."""
        salt = secrets.token_hex(16)
        start = time.perf_counter()
        digest = hashlib.sha3_512(f"{channel}:{digest_payload}".encode()).hexdigest()
        signature = hashlib.blake2b(
            f"{digest}:{salt}:{self.active_key.private_material}".encode(),
            digest_size=64,
        ).hexdigest()
        latency_ms = (time.perf_counter() - start) * 1000
        message_id = hashlib.sha1(f"{channel}:{digest}".encode()).hexdigest()
        record = SignatureRecord(
            message_id=message_id,
            channel=channel,
            algorithm=self.active_key.algorithm,
            key_id=self.active_key.key_id,
            digest=digest,
            salt=salt,
            signature=signature,
            issued_at=time.time(),
            latency_ms=round(latency_ms, 3),
            valid=True,
        )
        self.history.append(record)
        return asdict(record)

    def verify_signature(self, payload: str, record: SignatureRecord) -> bool:
        """Verify a signature using the key that produced it."""
        key = self.keyring.get(record.key_id, self.active_key)
        expected_digest = hashlib.sha3_512(f"{record.channel}:{payload}".encode()).hexdigest()
        expected_signature = hashlib.blake2b(
            f"{expected_digest}:{record.salt}:{key.private_material}".encode(),
            digest_size=64,
        ).hexdigest()
        return secrets.compare_digest(expected_signature, record.signature)

    def describe_active_key(self) -> Dict[str, object]:
        created_at = datetime.fromtimestamp(self.active_key.created_at, tz=timezone.utc).isoformat()
        return {
            "key_id": self.active_key.key_id,
            "algorithm": self.active_key.algorithm,
            "created_at": created_at,
            "public_material": self.active_key.public_material[:24],
        }

    def recent_history(self, limit: int = 5) -> List[Dict[str, object]]:
        items = list(self.history)[-limit:]
        return [asdict(record) for record in items]


quantum_cipher = QuantumCipher()
