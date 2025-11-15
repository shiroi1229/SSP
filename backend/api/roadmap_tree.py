from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging

from backend.db.connection import get_db
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItem, RoadmapItemBase
from pydantic import BaseModel, Field

router = APIRouter(prefix="/roadmap")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoadmapTreeItem(RoadmapItem):
    children: List["RoadmapTreeItem"] = []

# Forward reference for recursive type
RoadmapTreeItem.model_rebuild()

@router.get("/tree", response_model=List[RoadmapTreeItem])
def get_roadmap_tree(db: Session = Depends(get_db)):
    """
    Retrieve all roadmap items and return them in a hierarchical tree structure.
    """
    logger.info("Attempting to retrieve roadmap items for tree structure.")
    try:
        db_items = db.query(DBRoadmapItem).all()
        
        # Convert SQLAlchemy models to Pydantic models
        pydantic_items = [RoadmapItem.model_validate(item) for item in db_items]

        # Build a dictionary for quick lookup by ID
        items_by_id: Dict[int, RoadmapTreeItem] = {item.id: RoadmapTreeItem(**item.model_dump()) for item in pydantic_items}

        # Build the tree
        root_items: List[RoadmapTreeItem] = []
        for item_id, item_tree in items_by_id.items():
            if item_tree.parent_id is None:
                root_items.append(item_tree)
            else:
                parent = items_by_id.get(item_tree.parent_id)
                if parent:
                    parent.children.append(item_tree)
                else:
                    # If parent not found, treat as root (or log an error)
                    logger.warning(f"Parent with ID {item_tree.parent_id} not found for item {item_tree.id}. Treating as root.")
                    root_items.append(item_tree)
        
        # Sort root items and their children (optional, but good for consistent display)
        # For now, a simple sort by version string. More complex sorting can be added later.
        root_items.sort(key=lambda x: x.version)
        for item in root_items:
            item.children.sort(key=lambda x: x.version)

        logger.info(f"Successfully built roadmap tree with {len(root_items)} root items.")
        return root_items

    except Exception as e:
        logger.error(f"Error building roadmap tree: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build roadmap tree: {e}")
