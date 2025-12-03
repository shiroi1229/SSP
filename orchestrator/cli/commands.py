# path: orchestrator/cli/commands.py
# version: v0.1
# purpose: Thin command handlers that wrap orchestrator subsystems for CLI use

from __future__ import annotations

from typing import Any, Dict, Optional

from modules.collective_intelligence_core import CollectiveIntelligenceCore
from modules.cognitive_graph_engine import CognitiveGraphEngine
from modules.distributed_persona_fabric import DistributedPersonaFabric
from modules.evolution_mirror import EvolutionMirror
from modules.log_manager import log_manager
from modules.self_reasoning_loop import SelfReasoningLoop


def run_evolution_mirror(mode: str = "reflect", event: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    mirror = EvolutionMirror()
    if mode == "observe" and event:
        mirror.observe(event, data or {})
        return {"status": "recorded", "event": event}
    return mirror.reflect()


def run_collective_intelligence(personas: int = 3, cycles: int = 2) -> Dict[str, Any]:
    core = CollectiveIntelligenceCore(personas=personas, cycles=cycles)
    return core.aggregate_decisions()


def run_persona_fabric(personas: int = 3, cycles: int = 2):
    fabric = DistributedPersonaFabric(persona_count=personas)
    results = []
    for _ in range(cycles):
        consensus = fabric.simulate_collective_thinking()
        results.append(consensus)
    return results


def run_self_reasoning(cycles: int = 3):
    loop = SelfReasoningLoop()
    records = []
    for _ in range(cycles):
        records.append(loop.loop_once())
    return records


def run_cognitive_graph(mode: str, src: Optional[str] = None, rel: Optional[str] = None, tgt: Optional[str] = None):
    engine = CognitiveGraphEngine()
    if mode == "add" and src and rel and tgt:
        engine.add_relation(src, rel, tgt)
        path = engine.export()
        log_manager.info("Cognitive graph relation added", extra={"src": src, "rel": rel, "tgt": tgt})
        return {"status": "added", "path": path}
    if mode == "path" and src and tgt:
        return engine.find_path(src, tgt)
    raise ValueError("Unsupported graph mode or missing parameters")
