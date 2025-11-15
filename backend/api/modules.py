
import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from backend.db.connection import get_db
from backend.api.roadmap_tree import get_roadmap_tree, RoadmapTreeItem

router = APIRouter()
logger = logging.getLogger(__name__)

MODULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'modules'))

# 手動マッピング: モジュールファイル名 -> ロードマップVer表記
MANUAL_VERSION_MAP: Dict[str, str] = {
    # コアAI
    "llm.py": "v2.0 Contract Core",
    "rag_engine.py": "v2.0 Contract Core",
    "generator.py": "v2.0 Contract Core",
    "evaluator.py": "v2.4 Impact Analyzer",
    "memory_store.py": "v0.5 Knowledge Viewer",
    "meta_contract_system.py": "v3.0 Meta Contract System",
    # 自己進化・最適化
    "self_optimizer.py": "v2.2 Multi-Module Optimization",
    "collective_optimizer.py": "v3.0 Meta Contract System",
    "collective_intelligence_core.py": "v3.5 Shared Reality Nexus",
    "self_intent.py": "v3.1 Co-Evolution Bridge",
    "self_reasoning_loop.py": "v3.5 Distributed Consciousness",
    "predictive_analyzer.py": "v2.8 Integrity Monitor",
    "predictive_trainer.py": "v2.8 Integrity Monitor",
    # ペルソナ・感情
    "persona_manager.py": "v0.9 Emotion Engine Expansion",
    "persona_evolver.py": "v2.3 Context Snapshot / Rollback",
    "emotion_engine.py": "v0.8 Emotion Engine / Stage UI",
    "emotion_modulation_network.py": "v0.9 Emotion Engine Expansion",
    "emotion_camera_sync_engine.py": "v0.8 Emotion Engine / Stage UI",
    "distributed_persona_fabric.py": "v3.5 Shared Reality Nexus",
    # メタ認知・内省
    "metacognition.py": "v2.4 Context Evolution Framework",
    "cognitive_graph_engine.py": "v1.2 Stage Orchestrator UI",
    "evolution_mirror.py": "v2.4 Context Evolution Framework",
    "impact_analyzer.py": "v2.5 Impact Analyzer / Auto Repair",
    # 自動監視・修復
    "anomaly_detector.py": "v2.8 Integrity Monitor",
    "auto_repair.py": "v2.5 Impact Analyzer / Auto Repair",
    "auto_fix_executor.py": "v2.5 Impact Analyzer / Auto Repair",
    "auto_sync_monitor.py": "v2.8 Integrity Monitor",
    "alert_dispatcher.py": "v2.3 Contract Validator",
    # ステージ関連
    "stage_director.py": "v1.2 Stage Orchestrator UI",
    "stage_recorder.py": "v1.2 Stage Orchestrator UI",
    "stage_memory.py": "v1.2 Stage Orchestrator UI",
    # 外部連携・ユーティリティ
    "config_manager.py": "v0.1 MVP Core",
    "log_manager.py": "v0.5 Knowledge Viewer",
    "embedding_utils.py": "v2.0 Contract Core",
    "script_parser.py": "v1.0 Self-Analysis Engine",
    "osc_bridge.py": "v0.2 TTS Manager",
    "tts_manager.py": "v0.2 TTS Manager",
    # メディア・レンダリング系（ステージUIに寄せる）
    "adaptive_color_grader.py": "v0.8 Emotion Engine / Stage UI",
    "adaptive_physics.py": "v0.8 Emotion Engine / Stage UI",
    "auto_pose_correction.py": "v0.8 Emotion Engine / Stage UI",
    "motion_translator.py": "v0.8 Emotion Engine / Stage UI",
    "smooth_transition_generator.py": "v0.8 Emotion Engine / Stage UI",
    "stereo_depth_enhancer.py": "v0.8 Emotion Engine / Stage UI",
    "render_cache_controller.py": "v0.8 Emotion Engine / Stage UI",
    "scene_layout_optimizer.py": "v0.8 Emotion Engine / Stage UI",
    "scene_acoustic_learner.py": "v0.8 Emotion Engine / Stage UI",
    "voice_performance_synthesizer.py": "v0.8 Emotion Engine / Stage UI",
    "emotion_modulation_network.py": "v0.8 Emotion Engine / Stage UI",
    "emotion_camera_sync_engine.py": "v0.8 Emotion Engine / Stage UI",
    # サンプル/補助
    "sample_generator.py": "v0.1 MVP Core",
    "render_cache_controller.py": "v0.8 Emotion Engine / Stage UI",
    # 予測/トレーニング補助
    "predictive_trainer.py": "v2.8 Integrity Monitor",
}

DEFAULT_ROADMAP_VERSION = "v0.1 MVP Core"


def get_module_description(file_path: str) -> str:
    """
    Extracts a description from the top of a Python file.
    Looks for a docstring or a comment block.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500) # Read first 500 chars
            
            # Try to find a module-level docstring
            docstring_match = re.search(r'^"""(.*?)"""', content, re.DOTALL | re.MULTILINE)
            if docstring_match:
                return docstring_match.group(1).strip().split('\n')[0]

            # If no docstring, look for a comment block
            comment_match = re.search(r'^# (.*)', content, re.MULTILINE)
            if comment_match:
                return comment_match.group(1).strip()

    except Exception:
        # If anything fails, just return a default string
        pass
    return "No description found."


def collect_modules(db: Session) -> List[Dict[str, Any]]:
    """Gather modules with roadmap versions."""
    logger.info("Fetching modules and associating with roadmap versions.")
    try:
        # 1. Get roadmap data
        roadmap_tree = get_roadmap_tree(db)
        
        # 2. Create a version map from the roadmap + manual overrides
        version_map: Dict[str, str] = {}
        def traverse(items: List[RoadmapTreeItem]):
            for item in items:
                search_text = ' '.join(
                    filter(None, [item.description, getattr(item, "details", None), getattr(item, "objective", None)] + (item.keyFeatures or []))
                )
                found_modules = re.findall(r'([a-zA-Z0-9_]+\.py)', search_text)
                for module_name in found_modules:
                    if module_name not in version_map:
                        version_map[module_name] = item.version
                if item.children:
                    traverse(item.children)
        traverse(roadmap_tree)

        # manual overrides take priority
        version_map.update(MANUAL_VERSION_MAP)

        # 3. Get modules from the filesystem
        module_files = [f for f in os.listdir(MODULES_DIR) if f.endswith('.py') and f != '__init__.py']

        # 4. Construct the response
        response_data: List[Dict[str, Any]] = []
        for module_name in sorted(module_files):
            module_path = os.path.join(MODULES_DIR, module_name)
            description = get_module_description(module_path)
            version = version_map.get(module_name, DEFAULT_ROADMAP_VERSION)
            response_data.append({
                "name": module_name,
                "description": description,
                "version": version
            })
            
        logger.info(f"Successfully processed {len(response_data)} modules.")
        return response_data

    except Exception as e:
        logger.error(f"Error fetching modules with versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch modules: {e}")


@router.get("/modules", response_model=List[Dict[str, Any]])
def get_modules_with_versions(db: Session = Depends(get_db)):
    """
    Retrieves all modules from the filesystem, extracts their descriptions,
    and associates them with a development version from the roadmap.
    """
    return collect_modules(db)
