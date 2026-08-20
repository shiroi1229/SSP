# path: cli/shiroi_cli.py
# version: v1

import argparse
import sys
import os
import json
import datetime
import asyncio

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.main import run_orchestrator_workflow
from backend.db.connection import save_session_to_db
from modules.evaluator import save_feedback
from modules.rag_engine import register_high_score_sample
from modules.tts_manager import TTSManager
from modules.emotion_parser import parse_emotion

tts_manager = TTSManager()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shiroi System Platform CLI for interactive feedback.")
    parser.add_argument("prompt", type=str, help="User input to the system.")
    parser.add_argument("--speak", action="store_true", help="Synthesize and play the response.")
    args = parser.parse_args()

    print("--- 初回生成: 開始 ---")
    initial_answer, context, original_user_input = run_orchestrator_workflow(args.prompt, interactive_feedback=True)
    print(f"シロイ: {initial_answer}")
    print("--- 初回生成: 終了 ---")
    if args.speak:
        emotion_info = parse_emotion(initial_answer)
        asyncio.run(tts_manager.speak(initial_answer, emotion=emotion_info['emotion_tags'][0]))


    # Interactive feedback
    try:
        while True:
            try:
                evaluation_score = float(input("評価スコア (0.0-1.0): "))
                if not (0.0 <= evaluation_score <= 1.0):
                    raise ValueError("スコアは0.0から1.0の範囲で入力してください。")
                break
            except ValueError as e:
                print(f"入力エラー: {e} もう一度入力してください。")

        evaluation_comment = input("評価コメント: ").strip() or "（コメントなし）"

        # Save final session log
        session_log_entry = {
            "user_input": original_user_input,
            "final_output": initial_answer,
            "evaluation_score": evaluation_score,
            "evaluation_comment": evaluation_comment,
            "workflow_trace": [{"module": "CLI_Interactive_Feedback", "iterations": 1}]
        }
        try:
            save_session_to_db(session_log_entry)
        except Exception as e:
            print(f"⚠ DB保存失敗: {e}")

        # 高スコア応答をRAGへ登録
        register_high_score_sample(original_user_input, initial_answer, evaluation_score, evaluation_comment)

        # 評価フィードバックをJSONファイルに保存
        save_feedback(original_user_input, initial_answer, evaluation_score, evaluation_comment)

        print(f"\n✅ フィードバックが記録されました。スコア: {evaluation_score}")

        # CLIインタラクションログを保存
        cli_log_entry = {
            "id": f"cli_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "cli_interaction",
            "context": {
                "user_input": original_user_input,
                "cli_command": f"python cli/shiroi_cli.py {args.prompt}",
            },
            "output": {
                "initial_answer": initial_answer,
                "evaluation_score": evaluation_score,
                "evaluation_comment": evaluation_comment,
            },
            "notes": "CLI経由での対話型フィードバック記録。"
        }

        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"cli_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        log_path = os.path.join(log_dir, log_filename)

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(cli_log_entry, f, ensure_ascii=False, indent=2)
        print(f"CLIインタラクションログを {log_path} に保存しました。")
    except KeyboardInterrupt:
        print("\nCLIセッションを中断しました。")
        sys.exit(0)