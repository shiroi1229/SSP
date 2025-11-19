import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Database connection details
# Assuming these are available as environment variables or hardcoded for this temporary script
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ssp_admin:Mizuho0824@localhost:5432/ssp_memory")

def add_parent_id_column():
    engine = None
    session = None
    try:
        logger.info(f"Attempting to connect to database: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        # Check if column already exists to prevent errors on re-run
        # This is a simplified check, a proper migration tool would be more robust
        result = session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='roadmap_items' AND column_name='parent_id';"
        )).fetchone()

        if result:
            logger.info("Column 'parent_id' already exists in 'roadmap_items' table. Skipping migration.")
        else:
            logger.info("Adding 'parent_id' column to 'roadmap_items' table...")
            session.execute(text("ALTER TABLE roadmap_items ADD COLUMN parent_id INTEGER;"))
            session.commit()
            logger.info("Column 'parent_id' added successfully.")
    except Exception as e:
        logger.error(f"Error adding parent_id column: {e}", exc_info=True)
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
        if engine:
            engine.dispose()

if __name__ == "__main__":
    add_parent_id_column()
