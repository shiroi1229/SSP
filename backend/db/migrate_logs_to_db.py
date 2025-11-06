# path: backend/db/migrate_logs_to_db.py
# version: v0.30
import os
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import sys

# Add the parent directory to sys.path to allow importing 'backend' as a package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.db.connection import SessionLocal, engine
from backend.db.models import Base, SessionLog
from modules.config_manager import load_environment # Import load_environment

# Load environment variables
config = load_environment()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs") # Adjust path to logs directory

def migrate_logs_to_db():
    print("--- Starting log migration to PostgreSQL ---")
    db = SessionLocal()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".json") and (filename.startswith("session_") or filename.startswith("feedback_session_")):
            filepath = os.path.join(LOGS_DIR, filename)
            session_id_str = filename.replace(".json", "")
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
                    
                    # Handle both single log entry and list of log entries (for feedback loop)
                    if isinstance(log_data, list):
                        # For feedback loop, process each entry
                        entries_to_migrate = log_data
                    else:
                        entries_to_migrate = [log_data]

                    for entry in entries_to_migrate:
                        # Generate a unique ID for each entry if it's a feedback loop retry
                        # Or use a hash of content if original ID is not unique enough
                        # For simplicity, let's use a combination of filename and retry_attempt
                        unique_id_base = session_id_str
                        if entry.get("retry_attempt") is not None:
                            unique_id_base += f"_{entry['retry_attempt']}"
                        
                        # Check if an entry with this ID already exists (simple check, can be improved)
                        # For now, we'll rely on the DB's primary key for uniqueness
                        
                        # Extract data, handling potential missing keys
                        timestamp_str = entry.get("timestamp")
                        if timestamp_str:
                            try:
                                # Handle different timestamp formats if necessary
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            except ValueError:
                                timestamp = datetime.utcnow() # Fallback
                        else:
                            timestamp = datetime.utcnow()

                        user_input = entry.get("user_input")
                        final_output = entry.get("final_output")
                        
                        evaluation_score = None
                        evaluation_comment = None
                        
                        # Extract score and comment, handling different structures
                        feedback = entry.get("feedback")
                        if isinstance(feedback, dict):
                            evaluation_score = feedback.get("score")
                            evaluation_comment = feedback.get("comment")
                        elif entry.get("evaluation_score") is not None: # For feedback loop logs
                            evaluation_score = entry.get("evaluation_score")
                            evaluation_comment = entry.get("evaluation_comment")

                        workflow_trace = entry.get("workflow_trace")
                        
                        new_log = SessionLog(
                            timestamp=timestamp,
                            user_input=user_input,
                            final_output=final_output,
                            evaluation_score=evaluation_score,
                            evaluation_comment=evaluation_comment,
                            workflow_trace=workflow_trace # SQLAlchemy's JSON type handles dicts
                        )
                        
                        db.add(new_log)
                        try:
                            db.commit()
                            migrated_count += 1
                        except IntegrityError:
                            db.rollback()
                            skipped_count += 1
                            print(f"Skipped duplicate entry from {filename}.")
                        except Exception as commit_e:
                            db.rollback()
                            error_count += 1
                            print(f"Error committing entry from {filename}: {commit_e}")

            except json.JSONDecodeError:
                error_count += 1
                print(f"Error: Could not decode JSON from {filename}")
            except Exception as e:
                error_count += 1
                print(f"Error processing {filename}: {e}")
    
    db.close()
    print(f"--- Log migration complete. Migrated: {migrated_count}, Skipped: {skipped_count}, Errors: {error_count} ---")

if __name__ == "__main__":
    migrate_logs_to_db()
