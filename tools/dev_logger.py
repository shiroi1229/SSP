# path: tools/dev_logger.py
# version: v0.2
import subprocess
import json
import datetime
import os
import sys

def main():
    devlogs_dir = os.path.join("D:\\gemini", "devlogs")
    os.makedirs(devlogs_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(devlogs_dir, f"session_{timestamp}.json")

    output_dir = os.path.join("D:\\gemini", "out")
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, f"{timestamp}_output.txt")

    # User-provided paths
    prompt_file_path = r"D:\\gemini\\prompts\\orchestrator_dev_log.txt"
    gemini_cli_path = r"C:\\Users\\shiro\\AppData\\Roaming\\npm\\gemini.cmd" # User's specified path
    model_name = "gemini-2.5-pro" # Example model name

    log_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model_name,
        "prompt_file": prompt_file_path,
        "stdout": "",
        "stderr": "",
        "returncode": -1,
        "error": None,
        "saved_file": None # New field for saved output
    }

    try:
        command = [
            gemini_cli_path, # Use the full path to gemini.cmd
            "-m", model_name,
            "-p", f"@{prompt_file_path}"
        ]
        print(f"Executing command: {' '.join(command)}")
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False # Do not raise an exception for non-zero exit codes
        )

        log_data["stdout"] = process.stdout
        log_data["stderr"] = process.stderr
        log_data["returncode"] = process.returncode

        # Save Gemini's stdout to a file
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(process.stdout)
        log_data["saved_file"] = output_file_path

    except FileNotFoundError:
        log_data["error"] = f"Gemini CLI command not found at {gemini_cli_path}. Make sure the path is correct."
        print(f"Error: {log_data['error']}", file=sys.stderr)
    except Exception as e:
        log_data["error"] = str(e)
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] Gemini session log saved → {log_file_path}")

if __name__ == "__main__":
    main()
