from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from collections import defaultdict
import logging # Import logging

from backend.db.connection import get_db
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItem, RoadmapData, RoadmapItemCreate, RoadmapItemBase

router = APIRouter(prefix="/api/roadmap")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/current", response_model=RoadmapData)
def get_current_roadmap(db: Session = Depends(get_db)):
    """
    Retrieve all roadmap items, categorized by type (backend, frontend, robustness).
    """
    logger.info("Attempting to retrieve all roadmap items from the database.")
    try:
        db_items = db.query(DBRoadmapItem).all()
        logger.info(f"Retrieved {len(db_items)} roadmap items.")
    except Exception as e:
        logger.error(f"Error retrieving roadmap items from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
    categorized_items: Dict[str, List[RoadmapItem]] = defaultdict(list)
    for item in db_items:
        try:
            # Update for Pydantic v2 compatibility: from_orm is deprecated, use model_validate
            pydantic_item = RoadmapItem.model_validate(item)
            # Determine category based on version prefix or other logic
            if pydantic_item.version.startswith("v"):
                categorized_items["backend"].append(pydantic_item)
            elif pydantic_item.version.startswith("UI-v"):
                categorized_items["frontend"].append(pydantic_item)
            elif pydantic_item.version.startswith("R-v"):
                categorized_items["robustness"].append(pydantic_item)
            # Add more categorization logic if needed
        except Exception as e:
            logger.error(f"Error processing roadmap item {item.version}: {e}", exc_info=True)
            # Depending on severity, you might want to skip this item or raise HTTPException
            continue # Skip problematic item

    logger.info("Roadmap items categorized successfully.")
    return RoadmapData(
        backend=categorized_items["backend"],
        frontend=categorized_items["frontend"],
        robustness=categorized_items["robustness"]
    )

@router.get("/{version}", response_model=RoadmapItem)
def get_roadmap_item_by_version(version: str, db: Session = Depends(get_db)):
    """
    Retrieve a single roadmap item by its version.
    """
    logger.info(f"Attempting to retrieve roadmap item by version: {version}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.version == version).first()
    if db_item is None:
        logger.warning(f"Roadmap item {version} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    
    try:
        # Update for Pydantic v2 compatibility: from_orm is deprecated, use model_validate
        pydantic_item = RoadmapItem.model_validate(db_item)
        logger.info(f"Successfully retrieved and validated roadmap item: {version}")
        return pydantic_item
    except Exception as e:
        logger.error(f"Error validating roadmap item {version}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing roadmap item: {e}")

@router.post("/", response_model=RoadmapItem)
def create_roadmap_item(item: RoadmapItemCreate, db: Session = Depends(get_db)):
    """
    Create a new roadmap item.
    """
    logger.info(f"Attempting to create a new roadmap item with version: {item.version}")
    db_item = DBRoadmapItem(**item.model_dump())
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Successfully created roadmap item: {db_item.version}")
        return RoadmapItem.model_validate(db_item)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating roadmap item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create roadmap item: {e}")

@router.put("/{item_id}", response_model=RoadmapItem)
def update_roadmap_item(item_id: int, item: RoadmapItemBase, db: Session = Depends(get_db)):
    """
    Update an existing roadmap item by its ID.
    """
    logger.info(f"Attempting to update roadmap item with ID: {item_id}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.id == item_id).first()
    if not db_item:
        logger.warning(f"Update failed: Roadmap item with ID {item_id} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    update_data = item.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    try:
        db.commit()
        db.refresh(db_item)
        logger.info(f"Successfully updated roadmap item ID: {item_id}")
        return RoadmapItem.model_validate(db_item)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating roadmap item ID {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update roadmap item: {e}")

from pydantic import BaseModel
import re

class RoadmapImportText(BaseModel):
    text: str

def parse_roadmap_text(text: str) -> dict:
    """Parses the structured text block into a dictionary."""
    data = {}
    lines = text.strip().split('\n')
    
    # Extract title and version from the first relevant line
    title_line = ""
    for l in lines:
        if l.strip().startswith("タイトル:"):
            title_line = l.strip()
            break
    
    if title_line:
        title_match = re.search(r'タイトル:\s*(.*)\s*\(v(\d+\.\d+)\)', title_line)
        if title_match:
            data['codename'] = title_match.group(1).strip()
            data['version'] = f"v{title_match.group(2).strip()}"

    # Use a simple state machine to parse key-value and multi-line fields
    current_key = None
    current_values = []
    key_map = {
        "目標": "goal",
        "概要": "description",
        "開始日": "startDate",
        "終了日": "endDate",
        "進捗": "progress",
        "担当": "owner",
        "ステータス": "status",
        "主要機能": "keyFeatures",
        "依存関係": "dependencies",
        "評価指標": "metrics"
    }

    # Find where the main content starts
    content_started = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("タイトル:"):
            content_started = True
            continue
        if not content_started:
            continue

        parts = line.split(':', 1)
        key_from_map = key_map.get(parts[0].strip()) if len(parts) > 0 else None

        if len(parts) == 2 and key_from_map:
            if current_key and current_values:
                if current_key in ["keyFeatures", "dependencies", "metrics"]:
                    data[current_key] = [v.strip().lstrip('-').strip() for v in current_values if v.strip()]
                else:
                    data[current_key] = "\n".join(current_values).strip()
            
            current_key = key_from_map
            current_values = [parts[1].strip()]
        elif current_key:
            current_values.append(line)

    if current_key and current_values:
        if current_key in ["keyFeatures", "dependencies", "metrics"]:
            data[current_key] = [v.strip().lstrip('-').strip() for v in current_values if v.strip()]
        else:
            data[current_key] = "\n".join(current_values).strip()

    if 'progress' in data and isinstance(data['progress'], str):
        data['progress'] = int(data['progress'].replace('%', '').strip())
    
    # Set defaults for missing optional fields
    optional_fields = ["startDate", "endDate", "progress", "keyFeatures", "dependencies", "metrics", "owner", "documentationLink", "prLink"]
    for field in optional_fields:
        if field not in data:
            data[field] = None if field not in ["keyFeatures", "dependencies", "metrics"] else []


    return data

@router.post("/import-text", response_model=RoadmapItem)
def import_roadmap_item_from_text(payload: RoadmapImportText, db: Session = Depends(get_db)):
    """
    Parses a raw text block to create a new roadmap item.
    """
    logger.info("Attempting to import roadmap item from text block.")
    try:
        parsed_data = parse_roadmap_text(payload.text)
        
        # Validate required fields
        required_fields = ['version', 'codename', 'goal', 'description', 'status']
        for field in required_fields:
            if field not in parsed_data or not parsed_data[field]:
                raise HTTPException(status_code=400, detail=f"Parsing error: Missing required field '{field}'")

        roadmap_item_create = RoadmapItemCreate(**parsed_data)
        
        db_item = DBRoadmapItem(**roadmap_item_create.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        logger.info(f"Successfully imported and created roadmap item: {db_item.version}")
        return RoadmapItem.model_validate(db_item)

    except HTTPException as he:
        logger.error(f"HTTP exception during text import: {he.detail}")
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing roadmap item from text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import roadmap item from text: {e}")


