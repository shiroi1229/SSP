# path: backend/dev/auto_priority_planner.py
# version: v1
"""
Gemini開発優先度プランナー
エラー・未完タスク・依存関係を解析して次の手を自動決定する
"""
import json, os

REPORT_PATH = "./reports/self_summary.json"

def plan_next_step():
    if not os.path.exists(REPORT_PATH):
        return ["Run full self_healing_runner first."]
    data = json.load(open(REPORT_PATH, encoding="utf-8"))
    issues = data.get("issues", 0)
    trend = data.get("trend", "")
    suggestions = []

    if issues > 0:
        suggestions.append("🛠 修復タスク継続: 再テストまたは依存関係見直し")
    elif "改善必要" in trend:
        suggestions.append("⚙️ スタビリティ改善: self_optimizerを再実行")
    else:
        suggestions.append("🚀 開発本筋再開: script_engine_v3 に戻る")

    suggestions.append("📊 次回フェーズ: Dashboard で進捗監視を有効化")
    with open("./reports/next_steps.json", "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2, ensure_ascii=False)
    return suggestions

if __name__ == "__main__":
    plan_next_step()
