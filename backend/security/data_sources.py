"""Real data extractors that feed the Quantum Safety Protocol."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from modules.distributed_recovery_manager import manager as recovery_manager
from modules.akashic_sync_manager import manager as akashic_manager

CONTEXT_HISTORY_PATH = Path("logs/context_history.json")
META_REGISTRY_PATH = Path("contracts/meta/meta_registry.json")
PREDICTIVE_CORRECTION_PATH = Path("logs/predictive_self_correction.json")


def _read_json(path: Path) -> object:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        sanitized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(sanitized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _load_context_entries(limit: int = 120) -> List[dict]:
    data = _read_json(CONTEXT_HISTORY_PATH)
    if not isinstance(data, list):
        return []
    return data[-limit:]


def _load_predictive_actions(limit: int = 50) -> List[dict]:
    data = _read_json(PREDICTIVE_CORRECTION_PATH)
    if not isinstance(data, list):
        return []
    return data[-limit:]


def _load_meta_registry() -> dict:
    data = _read_json(META_REGISTRY_PATH)
    return data or {}


def _minutes_since(ts: datetime | None, now: datetime) -> float:
    if not ts:
        return 9999
    delta = now - ts
    return max(0.0, delta.total_seconds() / 60.0)


def _status_from_drift(drift: float) -> str:
    if drift < 0.25:
        return "verified"
    if drift < 0.65:
        return "resyncing"
    return "rekeying"


def gather_channel_metrics(now: datetime | None = None) -> List[Dict[str, object]]:
    """
    Build channel metrics based on actual logs/configuration data.
    Returns entries containing details payloads that the IntegrityChecker can hash.
    """
    now = now or datetime.now(timezone.utc)
    entries: List[Dict[str, object]] = []

    # Awareness bus derived from context history updates.
    context_entries = _load_context_entries()
    akashic_events = [evt for evt in context_entries if evt.get("key") == "akashic_state"]
    latest_akashic = akashic_events[-1] if akashic_events else None
    akashic_ts = _parse_timestamp(latest_akashic.get("timestamp")) if latest_akashic else None
    minutes_since_akashic = _minutes_since(akashic_ts, now)
    akashic_drift = min(1.0, minutes_since_akashic / 120)
    entries.append(
        {
            "name": "awareness_bus",
            "payload": {
                "minutes_since_update": minutes_since_akashic,
                "recent_updates": len(akashic_events),
                "latest_snapshot": latest_akashic.get("new_value", {}) if latest_akashic else {},
            },
            "drift": round(akashic_drift, 3),
            "last_verified": akashic_ts.isoformat() if akashic_ts else None,
            "alerts": [] if akashic_drift < 0.7 else ["Awareness bus update is stale."],
        }
    )

    # Persona contracts derived from meta registry.
    registry = _load_meta_registry()
    contracts = registry.get("contracts", [])
    total_contracts = len(contracts) or 1
    inactive_contracts = len([c for c in contracts if c.get("status") not in {"active", "stable"}])
    missing_fields = sum(len(c.get("missing_fields", [])) for c in contracts)
    persona_drift = min(1.0, (inactive_contracts / total_contracts) + (missing_fields / (total_contracts * 5)))
    entries.append(
        {
            "name": "persona_contracts",
            "payload": {
                "inactive_contracts": inactive_contracts,
                "missing_fields": missing_fields,
                "total_contracts": total_contracts,
                "registry_generated_at": registry.get("generated_at"),
            },
            "drift": round(persona_drift, 3),
            "last_verified": registry.get("generated_at"),
            "alerts": [] if inactive_contracts == 0 else ["Contracts require attention."],
        }
    )

    # Robustness cluster derived from distributed recovery manager.
    recovery_state = recovery_manager.get_state()
    nodes = recovery_state.get("nodes", [])
    inactive_nodes = [node for node in nodes if node.get("status") not in {"active", "ready"}]
    robustness_drift = min(1.0, len(inactive_nodes) / max(len(nodes), 1))
    entries.append(
        {
            "name": "robustness_cluster",
            "payload": {
                "nodes": nodes,
                "inactive": inactive_nodes,
            },
            "drift": round(robustness_drift, 3),
            "last_verified": now.isoformat(),
            "alerts": [] if not inactive_nodes else [f"Inactive nodes: {[n.get('name') for n in inactive_nodes]}"],
        }
    )

    # Akashic gateway derived from Akashic Sync Manager + predictive corrections.
    loop_health = akashic_manager.loop_health_summary()
    predictive_actions = _load_predictive_actions()
    warnings_recent = len([action for action in predictive_actions if action.get("action") != "none"])
    akashic_drift = min(1.0, (loop_health["errors"] * 0.5 + loop_health["warnings"] * 0.25 + warnings_recent * 0.05) / 5)
    entries.append(
        {
            "name": "akashic_gateway",
            "payload": {
                "loop_health": loop_health,
                "predictive_actions": warnings_recent,
            },
            "drift": round(akashic_drift, 3),
            "last_verified": now.isoformat(),
            "alerts": [] if akashic_drift < 0.6 else ["Loop health degraded"],
        }
    )

    for entry in entries:
        entry["status"] = _status_from_drift(entry["drift"])
        entry["statement"] = f"{entry['name']} drift={entry['drift']} status={entry['status']}"

    return entries
