# path: backend/dev/dev_dashboard_data.py
# version: v1
"""
開発ダッシュボードデータ統合
各メトリクスと修復履歴をまとめてUI用JSONを生成
"""
import json, os
from pathlib import Path # 追加

def build_dashboard_data():
    data = {}
    paths = [
        "./logs/devstats/summary.json",
        "./reports/self_summary.json",
        "./reports/next_steps.json",
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                data[os.path.basename(p)] = json.load(f)
    
    # --- regen_attempt ログ記録の追加 ---
    feedback_log_path = Path("./data/feedback_log.json")
    if feedback_log_path.exists():
        try:
            with open(feedback_log_path, "r", encoding="utf-8") as f:
                feedback_data = json.load(f)
                regen_attempts = [entry for entry in feedback_data if entry.get("regeneration") == True]
                data["regen_attempts"] = regen_attempts
        except json.JSONDecodeError:
            print(f"⚠️ feedback_log.json が破損しています: {feedback_log_path}")
        except Exception as e:
            print(f"❌ feedback_log.json の読み込み中にエラーが発生しました: {e}")

    output = "./frontend/public/dashboard_data.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Dashboard data exported to {output}")

if __name__ == "__main__":
    build_dashboard_data()
