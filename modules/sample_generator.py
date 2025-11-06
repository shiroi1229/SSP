# modules/sample_generator.py
import os
import json
import datetime
from pathlib import Path
from modules.generator import generate_answer
from backend.db.connection import insert_sample

def generate_sample():
    prompt = "シロイの世界観に登場する新しい技術・人物・組織・場所を5件、日本語で出力して。"
    # Assuming generate_answer can take a prompt and return a result directly
    result = generate_answer(model="", context="", user_input=prompt)
    
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "prompt": prompt,
        "result": result
    }
    
    # Ensure the data/samples directory exists
    output_dir = Path("data/samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / f"sample_{int(datetime.datetime.now().timestamp())}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    insert_sample(data)
    print(f"Generated sample saved to {file_path} and inserted into DB.")

if __name__ == '__main__':
    generate_sample()