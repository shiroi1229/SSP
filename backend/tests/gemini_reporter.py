# path: backend/tests/gemini_reporter.py
# version: v1
"""
Gemini CLI専用: system_test結果を要約してコメントとして返す
"""

import json, sys

def summarize(report_path):
    with open(report_path, encoding="utf-8") as f:
        text = f.read()

    summary = {
        "status": "PASS" if "200" in text and "error" not in text.lower() else "WARN",
        "detected_issues": text.count("error"),
        "report_excerpt": text[:800]
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    summarize(sys.argv[1])
