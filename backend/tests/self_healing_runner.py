# path: backend/tests/self_healing_runner.py
# version: v1
"""
Gemini CLI用 自己診断テストランナー
バックエンド未起動エラー時、自動的にUvicornを再起動して再試行。
"""

import subprocess, time, requests, json
import os

# このファイルの場所を基準にプロジェクトルートを決定 (d:/gemini/backend/tests -> d:/gemini)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

def ensure_backend_running():
    # ログファイルをプロジェクトルート直下のlogsディレクトリに保存
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    uvicorn_log_out = os.path.join(logs_dir, "uvicorn_stdout.log")
    uvicorn_log_err = os.path.join(logs_dir, "uvicorn_stderr.log")

    try:
        requests.get("http://127.0.0.1:8000/api/persona/state", timeout=3)
        return True
    except:
        print("⚠️ Backend not running. Launching Uvicorn...")
        python_executable = os.sys.executable
        with open(uvicorn_log_out, "w") as out_file, open(uvicorn_log_err, "w") as err_file:
            env = os.environ.copy()
            env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
            subprocess.Popen([python_executable, "-m", "uvicorn", "backend.main:app", "--reload"], 
                             cwd=PROJECT_ROOT, 
                             stdout=out_file, 
                             stderr=err_file, 
                             env=env)
        time.sleep(20) # Increased timeout
        try:
            requests.get("http://127.0.0.1:8000/api/persona/state", timeout=5)
            return True
        except:
            print("❌ Failed to auto-start backend. Uvicorn logs:")
            if os.path.exists(uvicorn_log_out):
                with open(uvicorn_log_out, "r") as f:
                    print("--- STDOUT ---")
                    print(f.read())
            if os.path.exists(uvicorn_log_err):
                with open(uvicorn_log_err, "r") as f:
                    print("--- STDERR ---")
                    print(f.read())
            return False

if __name__ == "__main__":
    if ensure_backend_running():
        print("✅ Backend is ready. Proceeding with system_test...")
        # Ensure system_test.py is run with the correct Python executable
        python_executable = os.sys.executable
        # PYTHONPATHを環境変数に設定してサブプロセスを実行
        env = os.environ.copy()
        env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.run([python_executable, os.path.join(BACKEND_DIR, "tests", "system_test.py")], cwd=PROJECT_ROOT, env=env)
    else:
        print("❌ Failed to auto-start backend.")
