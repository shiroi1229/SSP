# path: modules/generator.py
# version: v2.2

import os
import json
import datetime
from pathlib import Path
from modules.log_manager import log_manager
from orchestrator.context_manager import ContextManager
from modules.llm import analyze_text

def generate_response(context_manager: ContextManager):
    """Generates a response based on data from the ContextManager and updates the context."""
    log_manager.debug("[Generator] Starting context-aware generation...")

    # Get data from context
    prompt = context_manager.get("short_term.prompt")
    rag_context = context_manager.get("short_term.rag_context") or ""
    history = context_manager.get("mid_term.chat_history", default=[])
    model_params = context_manager.get("long_term.model_params") or {}
    config = context_manager.get("long_term.config") or {}

    if not prompt:
        log_manager.error("[Generator] No prompt found in context.")
        return

    # Prepare and execute LLM call using the centralized llm module
    try:
        # 1. Construct the prompt and user content
        try:
            instruction_path = Path(__file__).parent.parent / "prompts" / "gemini_instruction.txt"
            gemini_instruction = instruction_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            log_manager.error("[Generator] prompts/gemini_instruction.txt not found.")
            context_manager.set("mid_term.generated_output", "Error: Instruction file not found.", reason="Generator error: instruction file missing")
            return

        system_prompt = gemini_instruction + "\n出力は日本語で、キャラクター 'シロイ' の一人称口調で回答してください。"
        
        # Combine history and current prompt for the user content
        user_content_parts = []
        for message in history:
            user_content_parts.append(f"{message['role']}: {message['content']}")
        
        user_content_parts.append(f"user: 質問: {prompt}\n\n参考情報:\n{rag_context}")
        full_user_content = "\n".join(user_content_parts)

        # 2. Call the centralized LLM function
        log_manager.debug("[Generator] Calling centralized llm.analyze_text...")
        # The llm module now handles persona augmentation, URL selection, and API call logic
        raw_output = analyze_text(
            text=full_user_content,
            prompt=system_prompt,
            model_params_override=model_params
        )
        log_manager.info(f"[Generator] Answer generated: {raw_output[:80]}...")

        # 3. Process and save the response
        # Check if the response is a JSON error message from llm.py
        try:
            # If it's a JSON string, it might be an error response
            error_data = json.loads(raw_output)
            if isinstance(error_data, dict) and 'trend' in error_data and 'LLM analysis failed' in error_data['trend']:
                 log_manager.error(f"[Generator] Received error from llm module: {error_data['suggestion']}")
                 context_manager.set("mid_term.generated_output", "Error: LLM call failed.", reason=f"Generator error: {error_data['suggestion']}")
                 return # Stop further processing
        except json.JSONDecodeError:
            # Not a JSON string, so it's a valid response content
            pass

        # Set output to context
        context_manager.set("mid_term.generated_output", raw_output, reason="LLM response generated")
        log_manager.info("[Generator] Successfully generated response and saved to context.")

        # Add optimization log entry
        optimization_log = context_manager.get("long_term.optimization_log") or []
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "module": "generator",
            "inputs": {
                "prompt": prompt,
                "rag_context_summary": rag_context[:100] + "..." if rag_context else "",
                "model_params": model_params
            },
            "output": {
                "generated_output_summary": raw_output[:100] + "..."
            }
        }
        optimization_log.append(log_entry)
        context_manager.set("long_term.optimization_log", optimization_log, reason="Appending generation results")

    except Exception as e:
        log_manager.error(f"[Generator] An unexpected error occurred during generation: {e}", exc_info=True)
        context_manager.set("mid_term.generated_output", "Error: An unexpected error occurred in Generator.", reason=f"Generator error: {e}")

