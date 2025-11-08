# path: modules/llm.py
# version: v1.5
import requests
import json
import os
import datetime
import logging
from modules.metacognition import log_introspection  # Import for metacognition logging

# ❌ 旧: 固定URL
# LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions")

LLM_SIMULATION_MODE = os.getenv("LLM_SIMULATION_MODE", "False").lower() == "true"
PARAM_FILE = "./config/model_params.json"
PERSONA_FILE = "./config/persona_profile.json"


def load_persona_traits():
    """Loads current persona traits from PERSONA_FILE or returns an empty dict."""
    if not os.path.exists(PERSONA_FILE):
        return {}
    try:
        with open(PERSONA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("traits", {})
    except json.JSONDecodeError as e:
        logging.error(f"Error loading persona profile from {PERSONA_FILE}: {e}. Using empty traits.")
        return {}


def apply_persona_to_prompt(prompt: str) -> str:
    """Applies persona traits to the given prompt."""
    traits = load_persona_traits()
    if not traits:
        return prompt
    personality_desc = ", ".join([f"{k}:{v}" for k, v in traits.items()])
    return f"[Personality traits: {personality_desc}]\n{prompt}"


def analyze_text(text: str, prompt: str, model_params_override: dict = None) -> str:
    """
    Calls a local LLM (e.g., LM Studio or Ollama) or runs in simulation mode.
    The LLM endpoint URL is dynamically determined (from .env or override).
    """
    log_introspection("input_received", f"User input: {text[:100]}..., Prompt: {prompt[:100]}...")

    # --- モデルパラメータのロード ---
    model_params = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1024}
    if os.path.exists(PARAM_FILE):
        try:
            with open(PARAM_FILE, "r", encoding="utf-8") as f:
                model_params.update(json.load(f))
        except json.JSONDecodeError as e:
            logging.error(f"Error loading model parameters from {PARAM_FILE}: {e}. Using default parameters.")

    if model_params_override:
        model_params.update(model_params_override)

    # --- Persona を付与 ---
    augmented_prompt = apply_persona_to_prompt(prompt)
    log_introspection("prompt_augmented", f"Augmented prompt: {augmented_prompt[:100]}...")

    # ✅ URLの決定（優先度: override > LOCAL_LLM_API_URL > デフォルト）
    llm_url = (
        model_params.get("llm_url")
        or os.getenv("LOCAL_LLM_API_URL")
        or "http://127.0.0.1:1234/v1"
    )
    log_introspection("llm_url_selected", f"Using endpoint: {llm_url}", confidence=0.9)

    headers = {"Content-Type": "application/json"}
    data = {
        "model": os.getenv("SSP_LOCAL_LLM_MODEL_NAME", "Meta-Llama-3-8B-Instruct-Q4_K_M-GGUF"),
        "messages": [
            {"role": "system", "content": augmented_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": model_params["temperature"],
        "top_p": model_params["top_p"],
        "max_tokens": model_params["max_tokens"]
    }

    if "response_format" in model_params:
        data["response_format"] = model_params["response_format"]

    # --- Simulationモード ---
    if LLM_SIMULATION_MODE:
        simulated_response = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_model": "Simulated LLM",
            "confidence": 0.85,
            "trend": f"LLM analysis of '{text[:50]}...' simulated. Temperature={model_params['temperature']}",
            "suggestion": f"Simulated suggestion based on {model_params['top_p']}"
        }
        log_introspection("final_output", f"Simulated LLM response: {simulated_response['trend'][:50]}...")
        return json.dumps(simulated_response, ensure_ascii=False, indent=2)

    # --- 実際のLLM呼び出し ---
    try:
        response = requests.post(f"{llm_url}/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        llm_response_content = response.json()["choices"][0]["message"]["content"]
        log_introspection("final_output_actual", f"Actual LLM response: {llm_response_content[:50]}...")
        return llm_response_content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling local LLM: {e}")
        log_introspection("llm_call_failed", f"Error: {e}", confidence=0.0)
        error_response = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_model": "Actual LLM",
            "confidence": 0.0,
            "trend": "LLM analysis failed due to connection error.",
            "suggestion": f"Please check LLM service at {llm_url}. Error: {str(e)}"
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)
