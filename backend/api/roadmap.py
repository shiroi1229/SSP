from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from collections import defaultdict
import logging # Import logging

from backend.db.connection import get_db
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItem, RoadmapData

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

# TODO: Add POST, PUT, DELETE endpoints for managing roadmap items (for admin use)