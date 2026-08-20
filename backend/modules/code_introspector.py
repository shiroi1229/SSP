# path: backend/modules/code_introspector.py
# version: v1
"""
コード内省モジュール
エラー情報とソースコードを解析し、変数定義、型、親要素を推論する。
"""
import json
import os
import re

def analyze_code_for_error(error_info: dict, file_path: str) -> dict:
    """
    エラー情報とファイルパスに基づいてコードを解析し、修正提案を生成する。
    """
    analysis_result = {
        "suspect_variable": None,
        "expected_type": None,
        "actual_type": None,
        "suggested_fix": None,
        "confidence": 0.0
    }

    if not os.path.exists(file_path):
        return analysis_result

    with open(file_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    error_message = error_info.get("message", "").lower()
    error_line = None
    if error_info.get("stack"):
        # Attempt to extract line number from stack trace
        match = re.search(r'at \S+ \((.+?):(\d+):\d+\)', error_info["stack"])
        if match:
            # file_name = match.group(1)
            error_line = int(match.group(2))

    if "map is not a function" in error_message:
        # Use regex to dynamically extract the variable name before '.map'
        match = re.search(r'(\w+)\.(map|forEach|filter)\s+is not a function', error_message)
        if match:
            suspect_variable = match.group(1)
            problem_method = match.group(2)
            analysis_result["suspect_variable"] = suspect_variable
            analysis_result["expected_type"] = "Array"
            analysis_result["actual_type"] = "Unknown/Object"
            analysis_result["suggested_fix"] = {
                "instruction": f"Wrap {suspect_variable}.{problem_method} in Array.isArray",
                "old_code": f"{suspect_variable}.{problem_method}((",
                "new_code": f"Array.isArray({suspect_variable}) ? {suspect_variable}.{problem_method}(("
            }
            analysis_result["confidence"] = 0.9
        else:
            # Fallback if regex doesn't match, but error message still indicates map issue
            analysis_result["suspect_variable"] = "unknown_array_like_variable"
            analysis_result["expected_type"] = "Array"
            analysis_result["actual_type"] = "Unknown/Object"
            analysis_result["suggested_fix"] = {
                "instruction": "Wrap array-like variable.map in Array.isArray",
                "old_code": ".map((", # Generic old code, might need more context
                "new_code": "Array.isArray(variable) ? variable.map((" # Generic new code
            }
            analysis_result["confidence"] = 0.7 # Lower confidence for generic fix

    # Further AST analysis would go here for more complex cases
    # For now, we'll keep it simple based on the example.

    return analysis_result

if __name__ == "__main__":
    # Example usage:
    dummy_error = {
        "message": "TypeError: logs.map is not a function",
        "filename": "components/LogsPanel.tsx",
        "stack": "TypeError: logs.map is not a function\n    at LogsPanel (components/LogsPanel.tsx:36:15)"
    }
    dummy_file_path = "D:\\gemini\\frontend\\components\\LogsPanel.tsx" # This should be the actual path

    analysis = analyze_code_for_error(dummy_error, dummy_file_path)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
