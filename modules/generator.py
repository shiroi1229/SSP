# path: modules/generator.py
# version: v2.2

import os
import json
import re
import urllib.request
import datetime
from pathlib import Path
from modules.log_manager import log_manager
from orchestrator.context_manager import ContextManager

def generate_response(context_manager: ContextManager):
    """Generates a response based on data from the ContextManager and updates the context."""
    log_manager.debug("[Generator] Starting context-aware generation...")

    # Get data from context
    prompt = context_manager.get("short_term.prompt")
    rag_context = context_manager.get("short_term.rag_context") or ""
    model_params = context_manager.get("long_term.model_params") or {}
    config = context_manager.get("long_term.config") or {}

    if not prompt:
        log_manager.error("[Generator] No prompt found in context.")
        return

    # Prepare LLM call
    model_name = config.get("SSP_LOCAL_LLM_MODEL_NAME", "Meta-Llama-3-8B-Instruct-Q4_K_M-GGUF")
    temperature = model_params.get("temperature", 0.7)
    
    try:
        instruction_path = Path(__file__).parent.parent / "prompts" / "gemini_instruction.txt"
        gemini_instruction = instruction_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log_manager.error("[Generator] prompts/gemini_instruction.txt not found.")
        context_manager.set("mid_term.generated_output", "Error: Instruction file not found.", reason="Generator error: instruction file missing")
        return

    system_content = gemini_instruction + "\n出力は日本語で、キャラクター 'シロイ' の一人称口調で回答してください。"
    prompt_messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"質問: {prompt}\n\n参考情報:\n{rag_context}"}
    ]

    lm_studio_url = config.get("LM_STUDIO_URL", "http://127.0.0.1:1234")
    full_url = f"{lm_studio_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": prompt_messages,
        "temperature": temperature
    }

    # Call LLM and handle response
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(full_url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            response_body = response.read().decode("utf-8", errors="ignore")
            
            # Extract content from LLM response
            try:
                response_data = json.loads(response_body)
                raw_output = response_data['choices'][0]['message']['content']
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                log_manager.error(f"[Generator] Could not parse LLM response JSON: {e}. Using raw body.")
                raw_output = response_body

            # Set output to context
            context_manager.set("mid_term.generated_output", raw_output, reason="LLM response generated")
            log_manager.info(f"[Generator] Successfully generated response and saved to context.")

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

    except urllib.error.URLError as e:
        log_manager.error(f"[Generator] LLM API Error: {e.reason}", exc_info=True)
        context_manager.set("mid_term.generated_output", "Error: LLM API connection failed.", reason="Generator error: LLM API connection failed")
    except Exception as e:
        log_manager.error(f"[Generator] An unexpected error occurred: {e}", exc_info=True)
        context_manager.set("mid_term.generated_output", "Error: An unexpected error occurred.", reason="Generator error: unexpected exception")
