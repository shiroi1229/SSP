# path: backend/modules/governor_core.py
# version: v1
"""
Governor Core (Decision Layer)
Analyzerの出力を評価し、修正方針を策定、auto_patcherに命令を送る。
"""
import json
import logging
import os
from typing import Dict, Any
from backend.modules.code_introspector import analyze_code_for_error
from backend.modules.auto_patcher import apply_patch

log_file = "./logs/governor_trace.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def make_decision_and_act(error_info: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    logger.info(f"[Governor] Analyzing error for {file_path}: {error_info.get('message')}")
    analysis = analyze_code_for_error(error_info, file_path)
    logger.info(f"[Governor] Analysis result: {json.dumps(analysis)}")

    decision_result = {
        "status": "no_action",
        "reason": "",
        "patch_applied": False,
        "suggestion": None,
        "confidence": analysis.get("confidence", 0.0)
    }

    confidence = analysis.get("confidence", 0.0)
    suggested_fix = analysis.get("suggested_fix")

    # Example policy: only apply patch if confidence is high
    if confidence > 0.8 and suggested_fix:
        logging.info(f"[Governor] Decision: Auto-patching suggested fix: {suggested_fix}")
        decision_result["status"] = "patch_recommended"
        decision_result["reason"] = "High confidence fix suggested by Analyzer."
        decision_result["suggestion"] = suggested_fix
        try:
            # Assuming suggested_fix contains old_code and new_code
            # This needs to be refined based on the actual structure of suggested_fix
            # For now, let's assume suggested_fix is a dict with 'old_code' and 'new_code'
            patch_status = apply_patch(file_path, suggested_fix["instruction"], suggested_fix["old_code"], suggested_fix["new_code"])
            decision_result["patch_applied"] = patch_status["status"] == "success"
            if decision_result["patch_applied"]:
                logging.info(f"[Governor] Patch applied to {file_path}")
            else:
                decision_result["status"] = "patch_failed"
                decision_result["reason"] = f"Patch application failed: {patch_status.get('error', 'Unknown error')}"
                logging.error(f"[Governor] Patch application failed: {patch_status}")
        except Exception as e:
            decision_result["status"] = "patch_failed"
            decision_result["reason"] = f"Patch application failed: {e}"
            logging.error(f"[Governor] Patch application failed: {e}")
    else:
        decision_result["status"] = "manual_review_required"
        decision_result["reason"] = "Low confidence or no specific fix suggested."
        logging.info(f"[Governor] Decision: Manual review required for {file_path}")

    return decision_result

if __name__ == "__main__":
    # Example usage:
    dummy_error = {
        "message": "TypeError: logs.map is not a function",
        "filename": "LogsPanel.tsx",
        "stack": "TypeError: logs.map is not a function\n    at LogsPanel (components/LogsPanel.tsx:36:15)"
    }
    # This path should be relative to the project root for code_introspector to find it
    dummy_file_path = "frontend/components/LogsPanel.tsx"

    decision = make_decision_and_act(dummy_error, dummy_file_path)
    print(json.dumps(decision, indent=2, ensure_ascii=False))
