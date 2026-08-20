from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/api", tags=["Logs"])

@router.get("/logs/recent")
def get_recent_logs():
    log_file_path = Path("./logs/introspection_trace.log")
    logs = []
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get the last 50 lines and reverse them to show newest first
                for line in reversed(lines[-50:]):
                    try:
                        log_data = json.loads(line.strip())
                        # Adapt the backend log format to the frontend's expected format
                        adapted_log = {
                            "timestamp": log_data.get("timestamp"),
                            "level": log_data.get("event", "INFO").upper(), # Rename 'event' to 'level' and uppercase
                            "message": log_data.get("message", "Log message not found.")
                        }
                        logs.append(adapted_log)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            # In case of a file read error, return an informative log entry
            return {"logs": [{
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"Failed to read log file: {e}"
            }]}
    return {"logs": logs}