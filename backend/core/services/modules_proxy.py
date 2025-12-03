# path: backend/core/services/modules_proxy.py
# version: v0.1
# purpose: Central facade re-exporting selected symbols from modules/ for API layer

from __future__ import annotations

# Each import guarded so partial failures don't break entire API surface.

def _safe_import(import_path: str, name: str):
    try:
        module = __import__(import_path, fromlist=[name])
        return getattr(module, name)
    except Exception:  # pragma: no cover
        def _missing(*_, **__):
            raise RuntimeError(f"Facade placeholder for {import_path}.{name} not available")
        return _missing

# Causal / Meta
generate_internal_dialogue = _safe_import('modules.internal_dialogue', 'generate_internal_dialogue')
generate_report = _safe_import('modules.causal_report', 'generate_report')
build_meta_causal_report = _safe_import('modules.meta_causal_report', 'build_meta_causal_report')
verify_causality = _safe_import('modules.causal_verifier', 'verify_causality')
trace_event = _safe_import('modules.causal_trace', 'trace_event')
ingest_from_history = _safe_import('modules.causal_ingest', 'ingest_from_history')
compute_long_term_bias = _safe_import('modules.bias_history', 'compute_long_term_bias')
detect_bias = _safe_import('modules.bias_detector', 'detect_bias')

# Graph / Insight
causal_graph = _safe_import('modules.causal_graph', 'causal_graph')
InsightLinker = _safe_import('modules.insight_linker', 'InsightLinker')
get_cognitive_graph_data = _safe_import('modules.metacognition', 'get_cognitive_graph_data')
get_latest_introspection_log = _safe_import('modules.metacognition', 'get_latest_introspection_log')

# Persona / Emotion
set_detailed_emotion_state = _safe_import('modules.persona_manager', 'set_detailed_emotion_state')
get_current_persona_state = _safe_import('modules.persona_manager', 'get_current_persona_state')
EmotionEngine = _safe_import('modules.emotion_engine', 'EmotionEngine')

# Continuum / Timeline / Stage
ContinuumCore = _safe_import('modules.continuum_core', 'ContinuumCore')
rebuilder = _safe_import('modules.timeline_rebuilder', 'rebuilder')
StageRecorder = _safe_import('modules.stage_recorder', 'StageRecorder')
StageDirector = _safe_import('modules.stage_director', 'StageDirector')
ScriptParser = _safe_import('modules.script_parser', 'ScriptParser')
StageMemoryManager = _safe_import('modules.stage_memory', 'StageMemoryManager')

# Robustness / Resilience / Recovery
manager_existential_resilience = _safe_import('modules.existential_resilience_manager', 'manager')
manager_distributed_recovery = _safe_import('modules.distributed_recovery_manager', 'manager')
manager_luminous_nexus = _safe_import('modules.luminous_nexus_manager', 'manager')
manager_akashic_sync = _safe_import('modules.akashic_sync_manager', 'manager')
capture_state_snapshot = _safe_import('modules.state_resync', 'capture_state_snapshot')
failure_logger = _safe_import('modules.failure_logger', 'failure_logger')
read_actions = _safe_import('modules.auto_action_log', 'read_actions')
compute_action_stats = _safe_import('modules.auto_action_analyzer', 'compute_action_stats')
rollback_manager = _safe_import('modules.context_rollback', 'rollback_manager')

# Load balancer
balancer = _safe_import('modules.adaptive_load_balancer', 'balancer')
CONFIG_PATH = _safe_import('modules.adaptive_load_balancer', 'CONFIG_PATH')

# Optimizer / History
read_optimizer_history = _safe_import('modules.optimizer_history', 'read_optimizer_history')
apply_self_optimization = _safe_import('modules.self_optimizer', 'apply_self_optimization')

# LLM / Embeddings
analyze_text = _safe_import('modules.llm', 'analyze_text')
get_embedding = _safe_import('modules.embedding_utils', 'get_embedding')

# TTS / OSC
TTSManager = _safe_import('modules.tts_manager', 'TTSManager')
OSCBridge = _safe_import('modules.osc_bridge', 'OSCBridge')

# Alert / Diagnostic
AlertManager = _safe_import('modules.alert_manager', 'AlertManager')
DiagnosticEngine = _safe_import('modules.diagnostic_engine', 'DiagnosticEngine')

# Meta contracts
MetaContractManager = _safe_import('modules.meta_contract_system', 'MetaContractManager')

# Logs / Manager (log_manager provides instance log_manager)
log_manager = _safe_import('modules.log_manager', 'log_manager')

# World timeline
world_timeline_module = _safe_import('modules.world_timeline', 'world_timeline')  # may expose multiple funcs
fetch_world_timeline = _safe_import('modules.world_timeline', 'fetch_world_timeline')
fetch_world_event = _safe_import('modules.world_timeline', 'fetch_world_event')
create_world_event = _safe_import('modules.world_timeline', 'create_world_event')
update_world_event = _safe_import('modules.world_timeline', 'update_world_event')
delete_world_event = _safe_import('modules.world_timeline', 'delete_world_event')

# Public re-export list (optional hint)
__all__ = [
    'generate_internal_dialogue','generate_report','build_meta_causal_report','verify_causality','trace_event',
    'ingest_from_history','compute_long_term_bias','detect_bias','causal_graph','InsightLinker',
    'get_cognitive_graph_data','get_latest_introspection_log','set_detailed_emotion_state','get_current_persona_state',
    'EmotionEngine','ContinuumCore','rebuilder','StageRecorder','StageDirector','ScriptParser','StageMemoryManager',
    'manager_existential_resilience','manager_distributed_recovery','manager_luminous_nexus','manager_akashic_sync',
    'capture_state_snapshot','failure_logger','read_actions','compute_action_stats','balancer','CONFIG_PATH',
    'read_optimizer_history','apply_self_optimization','analyze_text','get_embedding','TTSManager','OSCBridge',
    'AlertManager','DiagnosticEngine','MetaContractManager','log_manager',
    'world_timeline_module','fetch_world_timeline','fetch_world_event','create_world_event',
    'update_world_event','delete_world_event'
]
