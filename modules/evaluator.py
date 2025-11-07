# path: modules/evaluator.py
# version: v2.2

import json
import re
import datetime
from modules.generator import generate_response
from modules.log_manager import log_manager
from modules.config_manager import load_environment
from orchestrator.context_manager import ContextManager

def evaluate_output(context_manager: ContextManager):
    """Evaluates the quality of a response using an LLM, based on data in the ContextManager."""
    log_manager.debug("Starting context-aware evaluation...")
    
    config = load_environment()
    answer = context_manager.get("mid_term.generated_output")
    rag_context = context_manager.get("short_term.rag_context")

    if not answer:
        log_manager.error("[Evaluator] No response found in context to evaluate.")
        return

    evaluation_prompt = f"""出力は日本語で行ってください。以下の情報を元に、提供された回答を評価し、JSON形式で出力してください。評価基準は「世界観整合性 (0.0-1.0)」「回答の具体性 (0.0-1.0)」「文体の一貫性 (0.0-1.0)」とし、それぞれに点数を付けてください。最終的なratingはこれら3つの平均とします。

コンテキスト:
{rag_context}

回答:
{answer}

JSON形式の出力例:
{{
  "worldview_consistency": 0.9,
  "specificity": 0.8,
  "style_consistency": 0.7,
  "rating": 0.8,
  "feedback": "世界観の整合性が高く、具体的な回答でした。文体をもう少し統一すると、さらに良くなります。"
}}
"""

    # Set the evaluation prompt in the context for the generator to use.
    # Note: This temporarily overwrites the original user prompt in the short_term context.
    context_manager.set("short_term.prompt", evaluation_prompt, reason="Internal call for evaluation")

    llm_response = context_manager.get("mid_term.generated_output") # Get the generated response from the context
    log_manager.debug(f"[Evaluator] LLM evaluation response: {llm_response[:200]}...")

    json_str_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
    
    if json_str_match:
        try:
            evaluation_data = json.loads(json_str_match.group(0))
            log_manager.debug(f"[Evaluator] Parsed evaluation JSON: {evaluation_data}")
            
            w_c = evaluation_data.get("worldview_consistency", 0.0)
            spec = evaluation_data.get("specificity", 0.0)
            s_c = evaluation_data.get("style_consistency", 0.0)
            
            overall_rating = round((w_c + spec + s_c) / 3.0, 2)
            evaluation_data["rating"] = overall_rating

            # Set outputs to ContextManager with reasons
            context_manager.set("mid_term.evaluation_score", overall_rating, reason="LLM-based evaluation")
            context_manager.set("mid_term.evaluation_feedback", evaluation_data.get("feedback", ""), reason="LLM-based evaluation")

            # Create and save optimization log
            optimization_log = context_manager.get("long_term.optimization_log") or []
            
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "module": "evaluator",
                "evaluation_result": {
                    "rating": overall_rating,
                    "feedback": evaluation_data.get("feedback", "")
                },
                "evaluated_response": answer
            }
            optimization_log.append(log_entry)
            context_manager.set("long_term.optimization_log", optimization_log, reason="Appending evaluation results")

            log_manager.info(f"[Evaluator] Evaluation successful. Score: {overall_rating}")

        except (json.JSONDecodeError, KeyError) as e:
            log_manager.error(f"[Evaluator] Failed to parse LLM evaluation response: {e}. Raw LLM response: {llm_response}", exc_info=True)
            context_manager.set("short_term.error", f"Evaluator failed: {e}", reason="Error during evaluation")
    else:
        log_manager.error(f"[Evaluator] Could not extract JSON from LLM response: {llm_response}")