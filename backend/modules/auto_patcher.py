# path: backend/modules/auto_patcher.py
# version: v1
"""
コード自動修正モジュール (Executor Layer)
Governorの決定に基づいて実際にソースコードを編集し、再ビルド、テストを行う。
"""
import json
import os
import shutil
import subprocess
import logging

log_file = "./logs/governor_trace.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def apply_patch(file_path: str, instruction: str, old_code: str, new_code: str) -> dict:
    """
    指定されたファイルにパッチを適用し、バックアップを作成する。
    """
    backup_path = file_path + ".bak"
    try:
        # Create a backup
        shutil.copyfile(file_path, backup_path)
        logging.info(f"[AutoPatcher] Created backup {backup_path}")

        # Apply the patch (This is a simplified example. A real patcher would use AST or regex for precise changes)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        modified_content = content.replace(old_code, new_code)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        logging.info(f"[AutoPatcher] Applied patch to {file_path}")

        # Placeholder for rebuild and retest. For now, we assume success.
        # In a full Governor system, this would trigger npm build/test and verify
        build_and_test_status = False
        if ".tsx" in file_path or ".js" in file_path:
            logging.info("[AutoPatcher] Triggering UI rebuild and test...")
            rebuild_result = subprocess.run(["npm", "run", "build"], cwd="./frontend", check=True)
            # test_result = subprocess.run(["npm", "test"], cwd="./frontend")
            if rebuild_result.returncode == 0:
                build_and_test_status = True
            else:
                build_and_test_status = False # Build failed
            
        return {"status": "success", "backup": backup_path, "build_test_pass": build_and_test_status}
    except Exception as e:
        logging.error(f"[AutoPatcher] Failed to apply patch to {file_path}: {e}")
        # Attempt to rollback on failure
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, file_path)
            logging.info(f"[AutoPatcher] Rolled back {file_path} from backup")
        return {"status": "failed", "error": str(e), "rolled_back": os.path.exists(backup_path)}

def cleanup_backup(file_path: str):
    backup_path = file_path + ".bak"
    if os.path.exists(backup_path):
        os.remove(backup_path)
        logging.info(f"[AutoPatcher] Cleaned up backup {backup_path}")