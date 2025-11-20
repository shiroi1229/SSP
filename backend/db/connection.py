# path: backend/db/connection.py
# version: v0.30
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text # Import text
from sqlalchemy.orm import sessionmaker
import psycopg2
import os
import datetime
from pathlib import Path # Add this import
import json # Add this import
from modules.config_manager import load_environment # Import the new function
from modules.log_manager import log_manager # Import log_manager
from backend.db.models import SessionLog, Sample, Base, DevLog, RoadmapItem, AwarenessSnapshot, InternalDialogue # Import SessionLog, Sample, Base, DevLog, and RoadmapItem models

# Load environment variables
config = load_environment()

# Construct the database URL using loaded config
DATABASE_URL = (
    f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@"
    f"{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DB']}"
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Tests the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        log_manager.info("PostgreSQL connection successful!")
        return True
    except Exception as e:
        log_manager.error(f"PostgreSQL connection failed: {e}")
        return False

def create_all_tables():
    """Creates all tables defined in Base.metadata."""
    try:
        Base.metadata.create_all(engine)
        log_manager.info("All tables created successfully!")
    except Exception as e:
        log_manager.exception(f"Failed to create tables: {e}")

def save_session_to_db(session_log_dict: dict):
    """Saves or updates a session log in the database using a dictionary."""
    db = SessionLocal()
    try:
        # The dictionary from the orchestrator might contain keys not in the model
        # Map 'id' from dict to SessionLog.id
        model_data = session_log_dict.copy()
        session_id_from_dict = model_data.pop('id', None) or model_data.pop('session_id', None)
        if session_id_from_dict:
            model_data['id'] = session_id_from_dict

        log_entry = SessionLog(**model_data)
        
        db.merge(log_entry) # Use merge to handle both insert and update
        db.commit()
        log_manager.info(f"✅ セッションログをPostgreSQLに保存/更新しました (id={log_entry.id})")
    except Exception as e:
        db.rollback()
        log_manager.exception(f"❌ Failed to save session log to PostgreSQL: {e}")
    finally:
        db.close()

def save_dev_log_to_db(dev_log_dict: dict):
    """Saves a development log in the database using a dictionary."""
    db = SessionLocal()
    try:
        dev_log_entry = DevLog(**dev_log_dict)
        db.merge(dev_log_entry)
        db.commit()
        log_manager.info(f"✅ 開発ログをPostgreSQLに保存/更新しました (id={dev_log_entry.id})")
    except Exception as e:
        db.rollback()
        log_manager.exception(f"❌ Failed to save development log to PostgreSQL: {e}")
    finally:
        db.close()

def insert_sample(sample_data: dict):
    db = SessionLocal()
    try:
        created_at_dt = None
        if "timestamp" in sample_data and isinstance(sample_data["timestamp"], str):
            try:
                created_at_dt = datetime.datetime.fromisoformat(sample_data["timestamp"])
            except ValueError:
                pass
        if not created_at_dt:
            created_at_dt = datetime.datetime.utcnow()

        db_sample = Sample(
            created_at=created_at_dt,
            prompt=sample_data.get("prompt"),
            result=sample_data.get("result")
        )

        db.add(db_sample)
        db.commit()
        db.refresh(db_sample)
        log_manager.info(f"✅ Sample {db_sample.id} successfully inserted into PostgreSQL.")
    except Exception as e:
        db.rollback()
        log_manager.exception(f"❌ Failed to insert sample into PostgreSQL: {e}")
    finally:
        db.close()

def get_latest_samples(limit: int = 50):
    """Retrieves the latest samples from the database."""
    db = SessionLocal()
    try:
        samples = db.query(Sample).order_by(Sample.created_at.desc()).limit(limit).all()
        log_manager.debug(f"Retrieved {len(samples)} latest samples from PostgreSQL.")
        return samples
    except Exception as e:
        log_manager.exception(f"❌ Failed to retrieve samples from PostgreSQL: {e}")
        return []
    finally:
        db.close()

def update_session_logs_table():
    """Adds missing columns to the session_logs table."""
    try:
        with engine.connect() as connection:
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS context TEXT"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS generator_prompt TEXT"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS generator_response TEXT"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS commit_hash VARCHAR(40)"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS env_snapshot TEXT"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS ai_comment TEXT"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS error_tag VARCHAR"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS impact_level VARCHAR"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS status_code INTEGER"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS response_time_ms INTEGER"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS log_persist_failed INTEGER DEFAULT 0"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS regeneration_attempts INTEGER DEFAULT 0"))
            connection.execute(text("ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS regeneration_success BOOLEAN DEFAULT FALSE"))
            # Commit the transaction to make the changes persistent
            connection.commit()
            log_manager.info("Updated table session_logs with new columns.")
    except Exception as e:
        log_manager.exception(f"Failed to update session_logs table: {e}")

def update_roadmap_items_table():
    """Adds the development_details column to the roadmap_items table."""
    try:
        with engine.connect() as connection:
            connection.execute(text("ALTER TABLE roadmap_items ADD COLUMN IF NOT EXISTS development_details TEXT"))
            connection.commit()
            log_manager.info("Updated table roadmap_items with new column 'development_details'.")
    except Exception as e:
        log_manager.exception(f"Failed to update roadmap_items table: {e}")

def ensure_awareness_snapshot_table():
    """Ensures the awareness_snapshots table exists."""
    ddl = """
    CREATE TABLE IF NOT EXISTS awareness_snapshots (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        backend_state JSONB,
        frontend_state JSONB,
        robustness_state JSONB,
        awareness_summary TEXT,
        context_vector JSONB
    );
    """
    try:
        with engine.connect() as connection:
            connection.execute(text(ddl))
            connection.commit()
            log_manager.info("Ensured awareness_snapshots table exists.")
    except Exception as e:
        log_manager.exception(f"Failed to ensure awareness_snapshots table: {e}")

def ensure_internal_dialogue_table():
    """Ensures the internal_dialogues table exists."""
    ddl = """
    CREATE TABLE IF NOT EXISTS internal_dialogues (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        participants JSONB,
        transcript JSONB,
        insights TEXT,
        source_snapshot_id INTEGER,
        meta JSONB
    );
    """
    try:
        with engine.connect() as connection:
            connection.execute(text(ddl))
            connection.commit()
            log_manager.info("Ensured internal_dialogues table exists.")
    except Exception as e:
        log_manager.exception(f"Failed to ensure internal_dialogues table: {e}")

if __name__ == "__main__":
    log_manager.info("Running connection.py example usage.")
    test_connection()
    # The following lines are for development purposes to apply schema changes.
    update_session_logs_table()
    update_roadmap_items_table()
    ensure_awareness_snapshot_table()
    ensure_internal_dialogue_table()
