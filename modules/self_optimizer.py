# path: modules/self_optimizer.py
# version: v2.0 (Refactored for ContextManager)
"""
Self Optimizer module
- Parses self-analysis reports
- Detects performance trends
- Adjusts model parameters dynamically
"""

import re
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def apply_self_optimization(context_manager: object):
    """Applies self-optimization based on data from the context."""
    logging.info("[SelfOptimizer] Applying self-optimization...")

    # Get data from context
    report = context_manager.get('short_term.self_analysis_report')
    params = context_manager.get('long_term.model_params') or {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1024}
    optimization_log = context_manager.get('long_term.optimization_log') or []

    if not report:
        logging.warning("[SelfOptimizer] No self-analysis report found in the context.")
        return {
            "status": "skipped",
            "message": "No report found.",
            "params": params,
            "avg_score": None,
        }

    # Extract numeric indicators from the report
    avg_match = re.search(r"Average Evaluation Score:\s*(\d+\.?\d*)", report)
    avg_score = float(avg_match.group(1)) if avg_match else 0.0

    # Adjust based on score trend
    if avg_score < 3.0:
        params["temperature"] = min(1.0, params["temperature"] + 0.1)
        params["top_p"] = min(1.0, params["top_p"] + 0.05)
    elif avg_score > 4.5:
        params["temperature"] = max(0.5, params["temperature"] - 0.1)
        params["top_p"] = max(0.7, params["top_p"] - 0.05)

    # Log optimization result
    optimization_log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "avg_score_at_optimization": avg_score,
        "new_parameters": params,
    }
    optimization_log.append(optimization_log_entry)

    # Set updated data back to context
    context_manager.set('long_term.model_params', params)
    context_manager.set('long_term.optimization_log', optimization_log)

    logging.info(f"[SelfOptimizer] Updated model parameters: {params}")
    return {"status": "success", "params": params, "avg_score": avg_score}
