# path: backend/tests/gemini_reporter_v3.py
# version: v1
"""
Gemini自己修復レポーター v3
→ 差分解析＋信頼スコア＋再学習トリガ＋Governor修復統計
"""
import json, sys, os

def summarize(path):
    text = open(path, encoding="utf-8").read()
    issues = text.count("error") + text.count("404") + text.count("exception")
    status = "PASS" if issues == 0 else "WARN"
    diff = "（安定）" if issues == 0 else "（改善必要）"

    # Placeholder for Governor specific metrics
    governor_fixes = 0 # This would be read from governor_trace.log or similar
    auto_rollback = False # This would be read from governor_trace.log or similar
    confidence_avg = 0.0 # This would be calculated from governor_trace.log or similar

    report = {
        "status": status,
        "issues": issues,
        "trend": diff,
        "summary_excerpt": text[:500],
        "governor_fixes": governor_fixes,
        "auto_rollback": auto_rollback,
        "confidence_avg": confidence_avg,
    }
    with open("./reports/self_summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    summarize(sys.argv[1])
