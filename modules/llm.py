import requests
import json
import os
import datetime
import logging

from modules.metacognition import log_introspection # Import for metacognition logging

LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions") # Default for LM Studio
LLM_SIMULATION_MODE = os.getenv("LLM_SIMULATION_MODE", "False").lower() == "true"
PARAM_FILE = "./config/model_params.json"
PERSONA_FILE = "./config/persona_profile.json"

def load_persona_traits():
    """
    Loads current persona traits from PERSONA_FILE or returns an empty dict.
    """
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
    """
    Applies persona traits to the given prompt.
    """
    traits = load_persona_traits()
    if not traits:
        return prompt
    personality_desc = ", ".join([f"{k}:{v}" for k, v in traits.items()])
    return f"[Personality traits: {personality_desc}]\n{prompt}"

def analyze_text(text: str, prompt: str, model_params_override: dict = None) -> str:
    """
    Simulates calling a local LLM (e.g., LM Studio) or Gemini API to analyze text.
    Returns a JSON structured string.
    """
    log_introspection("input_received", f"User input: {text[:100]}..., Prompt: {prompt[:100]}...")

    # Load current model parameters
    model_params = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1024} # Default values
    if os.path.exists(PARAM_FILE):
        try:
            with open(PARAM_FILE, "r", encoding="utf-8") as f:
                loaded_params = json.load(f)
                model_params.update(loaded_params)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading model parameters from {PARAM_FILE}: {e}. Using default parameters.")

    # Apply override if provided
    if model_params_override:
        model_params.update(model_params_override)

    # Apply persona to the prompt
    augmented_prompt = apply_persona_to_prompt(prompt)
    log_introspection("prompt_augmented", f"Augmented prompt: {augmented_prompt[:100]}...")

    # In a real scenario, this would involve making an API call to an LLM.
    url = LLM_API_URL
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": [
            {"role": "system", "content": augmented_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": model_params["temperature"],
        "top_p": model_params["top_p"],
        "max_tokens": model_params["max_tokens"]
    }
    # TODO: Future Improvement: Reflect "collective_bias" in temperature adjustment during LLM response
    # (as a personality stabilization parameter) for more nuanced control.
    # TODO: Future Improvement: Extend apply_persona_to_prompt to influence "speech style" for a more "personal AI".
    try:
        if LLM_SIMULATION_MODE:
            # Step 1: Hypothesis
            inner_thought = f"Question interpretation: '{text[:50]}...' に潜む感情を推定中。"
            log_introspection("inner_thought", inner_thought, confidence=0.8)

            # Step 2: Self-evaluation
            self_eval = "回答生成に先立ち感情的バランスを整える。"
            log_introspection("self_evaluation", self_eval, confidence=0.9)

            # Simulated LLM response in JSON format
            simulated_response = {
                "timestamp": datetime.datetime.now().isoformat(),
                "source_model": "Simulated LLM", # In a real scenario, this would be the actual model name
                "confidence": 0.85, # Simulated confidence score
                "trend": f"LLM analysis of comments: '{text[:50]}...' shows a trend of [Simulated Trend]. Current temp: {model_params['temperature']}",
                "suggestion": f"Based on this, it is suggested to [Simulated Suggestion] to improve performance. Current top_p: {model_params['top_p']}"
            }
            log_introspection("final_output", f"Simulated LLM response generated. Trend: {simulated_response['trend'][:50]}...")
            return json.dumps(simulated_response, ensure_ascii=False, indent=2)
        else:
            # Actual LLM call
            try:
                # Append response_format if present in model_params
                if "response_format" in model_params:
                    data["response_format"] = model_params["response_format"]

                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status() # Raise an exception for HTTP errors
                llm_response_content = response.json()["choices"][0]["message"]["content"]
                log_introspection("final_output_actual", f"Actual LLM response generated. Content: {llm_response_content[:50]}...")
                return llm_response_content
            except requests.exceptions.RequestException as e:
                logging.error(f"Error calling local LLM: {e}")
                log_introspection("llm_call_failed", f"Error: {e}", confidence=0.0)
                error_response = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "source_model": "Actual LLM",
                    "confidence": 0.0,
                    "trend": "LLM analysis failed due to connection error.",
                    "suggestion": f"Please check LLM service at {LLM_API_URL}. Error: {str(e)}"
                }
                return json.dumps(error_response, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling local LLM: {e}")
        log_introspection("llm_call_failed", f"Error: {e}", confidence=0.0)
        error_response = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_model": "Simulated LLM",
            "confidence": 0.0, # No confidence on error
            "trend": "LLM analysis failed due to connection error.",
            "suggestion": f"Please check LLM service at {LLM_API_URL}. Error: {str(e)}"
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"An unexpected error occurred during LLM analysis: {e}")
        log_introspection("llm_call_failed", f"Unexpected error: {e}", confidence=0.0)
        error_response = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_model": "Simulated LLM",
            "confidence": 0.0, # No confidence on error
            "trend": "LLM analysis failed due to unexpected error.",
            "suggestion": f"Error: {str(e)}"
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)
