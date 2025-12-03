# modules/llm.py
"""
ローカル Transformers モデル (Meta-Llama-3-8B-Instruct) を使った LLM 推論ラッパー
"""
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

_model = None
_tokenizer = None
_pipe = None

def _load_model():
    global _model, _tokenizer, _pipe
    if _model is None or _tokenizer is None or _pipe is None:
        _tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
        _model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        _pipe = pipeline("text-generation", model=_model, tokenizer=_tokenizer, device=0 if torch.cuda.is_available() else -1)

# API: analyze_text(text, prompt) -> str

def analyze_text(text: str, prompt: str = None) -> str:
    """
    指定テキストとプロンプトで LLM 推論を実行し、応答を返す
    """
    _load_model()
    input_text = prompt or text
    result = _pipe(input_text, max_new_tokens=512, temperature=0.8, top_p=0.95)
    return result[0]["generated_text"]
