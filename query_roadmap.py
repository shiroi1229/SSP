
import sys
import os
import json
from sqlalchemy.orm import class_mapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to Python path to allow module imports
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Assuming the connection and models are in the backend directory
from backend.db.models import RoadmapItem, Base

# In-memory SQLite database for standalone script execution
# This avoids dependency on the full backend stack for a simple query
DATABASE_URL = "postgresql://postgres:password@localhost:5432/ssp"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance to a dictionary."""
    mapper = class_mapper(model_instance.__class__)
    data = {}
    for column in mapper.columns:
        value = getattr(model_instance, column.key)
        # Convert array types to list for JSON serialization
        if "ARRAY" in str(column.type):
            value = list(value) if value else []
        data[column.key] = value
    return data

def get_roadmap_data():
    """Fetches all roadmap items from the database and returns them as a list of dicts."""
    # Create table if it doesn't exist (for standalone context)
    # Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Query and order by version
        roadmap_items = db.query(RoadmapItem).order_by(RoadmapItem.version).all()
        return [model_to_dict(item) for item in roadmap_items]
    finally:
        db.close()

if __name__ == "__main__":
    try:
        roadmap_data = get_roadmap_data()
        # Pretty print the JSON output
        print(json.dumps(roadmap_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the PostgreSQL database is running and accessible at {DATABASE_URL}.")
        print("You might need to install psycopg2-binary: pip install psycopg2-binary")

