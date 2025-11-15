from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from collections import defaultdict
from modules.log_manager import log_manager
import re
import json # Added json import

from backend.db.connection import get_db
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import (
    RoadmapItem,
    RoadmapData,
    RoadmapItemCreate,
    RoadmapItemBase,
    RoadmapItemUpdateByVersion,
    RoadmapPrefixSummary,
    RoadmapStatsResponse,
    RoadmapDelayedItem,
)

from pydantic import BaseModel # Moved from lower down
# import re # Already imported above

class RoadmapImportText(BaseModel): # Moved from lower down
    text: str

def parse_roadmap_text(text: str) -> dict:
    """Parses the structured text block into a dictionary."""
    
    # Handle the wrapper if it exists
    if text.strip().startswith('create_roadmap_entry """'):
        text = text.strip().replace('create_roadmap_entry """', '', 1)
        text = text.rsplit('"""', 1)[0]

    data = {}
    lines = text.strip().split('\n')
    
    # Extract title and version from the first relevant line
    title_line = ""
    for l in lines:
        if l.strip().startswith("タイトル:"):
            title_line = l.strip()
            break
    
    if title_line:
        title_match = re.search(r'タイトル:\s*(.*)\s*\((.*)\)', title_line)
        if title_match:
            data['codename'] = title_match.group(1).strip()
            data['version'] = title_match.group(2).strip()

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
        "評価指標": "metrics",
        "開発詳細指示": "development_details"
    }

    list_keys = ["keyFeatures", "dependencies", "metrics"]
    current_key = None
    current_values = []
    
    for line in lines:
        line = line.strip()

        # Check if the line starts with a known key
        found_new_key = False
        for k_jp, k_en in key_map.items():
            if line.startswith(k_jp + ":"):
                # If a new key is found, first save the values for the previous key
                if current_key and current_values:
                    if current_key in list_keys:
                        data[current_key] = [v.strip().lstrip('-').strip() for v in current_values if v.strip()]
                    else:
                        data[current_key] = "\n".join(current_values).strip()
                
                current_key = k_en
                current_values = []
                found_new_key = True
                
                # The value starts on the same line, after the colon
                value_part = line.split(':', 1)[1].strip()
                if value_part:
                    current_values.append(value_part)
                break # Found a key, move to next line
        
        if not found_new_key:
            # This line is not a new key. If we have an active key and the line isn't blank,
            # it's a value for the current key.
            if current_key and line:
                current_values.append(line)

    # After the loop, save the values for the last key
    if current_key and current_values:
        if current_key in list_keys:
            data[current_key] = [v.strip().lstrip('-').strip() for v in current_values if v.strip()]
        else:
            data[current_key] = "\n".join(current_values).strip()

    if 'progress' in data and isinstance(data['progress'], str):
        progress_match = re.search(r'\d+', data['progress'])
        if progress_match:
            data['progress'] = int(progress_match.group(0))
    
    # Set defaults for missing optional fields
    optional_fields = ["startDate", "endDate", "progress", "keyFeatures", "dependencies", "metrics", "owner", "documentationLink", "prLink", "development_details"]
    for field in optional_fields:
        if field not in data:
            data[field] = [] if field in list_keys else None

    return data

router = APIRouter(prefix="/roadmap")


def _split_and_clean_list_field(field_value: str | List[str] | None) -> List[str]:
    """Helper to split a string field into a list of cleaned strings, or return as-is if already a list."""
    if field_value is None:
        return []
    if isinstance(field_value, list):
        return [item.strip().lstrip('-').strip() for item in field_value if item.strip()]
    if isinstance(field_value, str):
        return [line.strip().lstrip('-').strip() for line in field_value.split('\n') if line.strip()]
    return []

def get_version_sort_key(item):
    """Creates a sort key for version strings like 'v1.0', 'UI-v0.5'."""
    version_str = item.version
    # Regex to capture an optional prefix (like 'UI-'), the major, and minor numbers
    match = re.match(r'([A-Z]+-)?v(\d+)\.(\d+)', version_str) # Fixed re.re.match to re.match
    
    if not match:
        # Fallback for any formats that don't match
        return (99, version_str)

    prefix, major, minor = match.groups()
    prefix = prefix or '' # Ensure prefix is a string

    # Define a sort order for known prefixes
    prefix_order = {
        '': 0,        # for 'vX.X'
        'UI-': 1,     # for 'UI-vX.X'
        'R-': 2,      # for 'R-vX.X'
    }
    
    prefix_num = prefix_order.get(prefix, 99)

    return (prefix_num, int(major), int(minor))

LIST_FIELDS = ("keyFeatures", "dependencies", "metrics")
OPTIONAL_STRING_FIELDS = ("owner", "documentationLink", "prLink", "startDate", "endDate", "development_details")


def _normalize_payload_fields(payload: Dict, fill_missing: bool = False) -> Dict:
    for field in LIST_FIELDS:
        if field in payload:
            payload[field] = _split_and_clean_list_field(payload[field])
        elif fill_missing:
            payload[field] = []
    for field in OPTIONAL_STRING_FIELDS:
        if field in payload and not payload[field]:
            payload[field] = None
        elif fill_missing and field not in payload:
            payload[field] = None
    return payload


def _validate_dependencies(dependencies: List[str], db: Session):
    if not dependencies:
        return
    existing_versions = {row[0] for row in db.query(DBRoadmapItem.version).all()}
    missing = [dep for dep in dependencies if dep not in existing_versions]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Dependencies not found: {', '.join(missing)}"
        )


def _get_prefix_from_version(version: str | None) -> str:
    if not version:
        return "UNKNOWN"
    return version.split('-', 1)[0] if '-' in version else version


def _coerce_progress(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@router.get("/stats", response_model=RoadmapStatsResponse)
def get_roadmap_stats(
    focus_prefix: str = Query("A", description="Prefix to surface in the delayed list."),
    db: Session = Depends(get_db),
):
    log_manager.info("Generating roadmap prefix summary.")
    try:
        db_items = db.query(DBRoadmapItem).all()
    except Exception as exc:
        log_manager.error(f"Failed to fetch roadmap stats: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    aggregates: Dict[str, Dict[str, int]] = defaultdict(lambda: {"count": 0, "completed": 0, "in_progress": 0, "not_started": 0})
    delayed_items: List[RoadmapDelayedItem] = []

    for item in db_items:
        prefix = _get_prefix_from_version(item.version)
        progress_value = _coerce_progress(item.progress)
        bucket = aggregates[prefix]
        bucket["count"] += 1
        if progress_value >= 100:
            bucket["completed"] += 1
        elif progress_value > 0:
            bucket["in_progress"] += 1
        else:
            bucket["not_started"] += 1

        if prefix == focus_prefix and progress_value < 100:
            delayed_items.append(
                RoadmapDelayedItem(
                    version=item.version,
                    codename=item.codename,
                    progress=item.progress,
                    status=item.status,
                )
            )

    ordered_summary = [
        RoadmapPrefixSummary(
            prefix=prefix,
            count=bucket["count"],
            completed=bucket["completed"],
            in_progress=bucket["in_progress"],
            not_started=bucket["not_started"],
        )
        for prefix, bucket in sorted(aggregates.items(), key=lambda kv: kv[0])
    ]

    return RoadmapStatsResponse(summary=ordered_summary, delayed=delayed_items)


@router.get("/current", response_model=RoadmapData)
def get_current_roadmap(db: Session = Depends(get_db)):
    """
    Retrieve all roadmap items, categorized and sorted by version.
    """
    log_manager.info("Attempting to retrieve all roadmap items from the database.")
    try:
        db_items = db.query(DBRoadmapItem).all()
        # Sort items using the custom version sort key
        db_items.sort(key=get_version_sort_key)
        log_manager.info(f"Retrieved and sorted {len(db_items)} roadmap items.")
    except Exception as e:
        log_manager.error(f"Error retrieving roadmap items from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
    categorized_items: Dict[str, List[RoadmapItem]] = defaultdict(list)
    for item in db_items:
        try:
            pydantic_item = RoadmapItem.model_validate(item)
            if pydantic_item.version.startswith("UI-v"):
                categorized_items["frontend"].append(pydantic_item)
            elif pydantic_item.version.startswith("R-v"):
                categorized_items["robustness"].append(pydantic_item)
            elif pydantic_item.version.startswith("A-v"):
                categorized_items["Awareness_Engine"].append(pydantic_item)
            else: # Default to backend for 'vX.X'
                categorized_items["backend"].append(pydantic_item)
        except Exception as e:
            log_manager.error(f"Error processing roadmap item {item.version}: {e}", exc_info=True)
            continue

    log_manager.info("Roadmap items categorized successfully.")
    return RoadmapData(
        backend=categorized_items["backend"],
        frontend=categorized_items["frontend"],
        robustness=categorized_items["robustness"],
        Awareness_Engine=categorized_items["Awareness_Engine"]
    )

@router.get("/{version}", response_model=RoadmapItem)
def get_roadmap_item_by_version(version: str, db: Session = Depends(get_db)):
    """
    Retrieve a single roadmap item by its version.
    """
    log_manager.info(f"Attempting to retrieve roadmap item by version: {version}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.version == version).first()
    if db_item is None:
        log_manager.warning(f"Roadmap item {version} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    
    try:
        # Manually construct the Pydantic model to ensure all fields are correctly mapped,
        # especially array types like keyFeatures.
        pydantic_item = RoadmapItem(
            id=db_item.id,
            version=db_item.version,
            codename=db_item.codename,
            goal=db_item.goal,
            status=db_item.status,
            description=db_item.description,
            startDate=db_item.startDate,
            endDate=db_item.endDate,
            progress=db_item.progress,
            keyFeatures=_split_and_clean_list_field(db_item.keyFeatures),
            dependencies=_split_and_clean_list_field(db_item.dependencies),
            metrics=_split_and_clean_list_field(db_item.metrics),
            owner=db_item.owner,
            documentationLink=db_item.documentationLink,
            prLink=db_item.prLink,
            development_details=db_item.development_details,
            parent_id=db_item.parent_id
        )
        log_manager.info(f"Successfully retrieved and validated roadmap item: {version}")
        return pydantic_item
    except Exception as e:
        log_manager.error(f"Error validating roadmap item {version}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing roadmap item: {e}")

@router.patch("/{version}", response_model=RoadmapItem)
def update_roadmap_item_by_version(
    version: str,
    item_update: RoadmapItemUpdateByVersion,
    db: Session = Depends(get_db)
):
    """
    Partially update an existing roadmap item by its version.
    """
    log_manager.info(f"Attempting to partially update roadmap item by version: {version}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.version == version).first()
    if not db_item:
        log_manager.warning(f"Update failed: Roadmap item with version {version} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    update_data = item_update.model_dump(exclude_unset=True, by_alias=True)
    _normalize_payload_fields(update_data, fill_missing=False)
    if "dependencies" in update_data:
        _validate_dependencies(update_data["dependencies"], db)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    try:
        db.commit()
        db.refresh(db_item)
        log_manager.info(f"Successfully updated roadmap item version: {version}")
        return RoadmapItem.model_validate(db_item)
    except Exception as e:
        db.rollback()
        log_manager.error(f"Error updating roadmap item version {version}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update roadmap item: {e}")

@router.post("/", response_model=RoadmapItem)
def create_roadmap_item(item: RoadmapItemCreate, db: Session = Depends(get_db)):
    """
    Create a new roadmap item.
    """
    log_manager.info(f"Attempting to create a new roadmap item with version: {item.version}")
    try:
        payload = _normalize_payload_fields(item.model_dump(by_alias=True), fill_missing=True)
        _validate_dependencies(payload.get("dependencies", []), db)
        db_item = DBRoadmapItem(**payload)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        log_manager.info(f"Successfully created roadmap item: {db_item.version}")
        return RoadmapItem.model_validate(db_item)
    except Exception as e:
        db.rollback()
        log_manager.error(f"Error creating roadmap item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create roadmap item: {e}")

@router.put("/{item_id}", response_model=RoadmapItem)
def update_roadmap_item(item_id: int, item: RoadmapItemBase, db: Session = Depends(get_db)):
    """
    Update an existing roadmap item by its ID.
    """
    log_manager.info(f"Attempting to update roadmap item with ID: {item_id}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.id == item_id).first()
    if not db_item:
        log_manager.warning(f"Update failed: Roadmap item with ID {item_id} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    update_data = _normalize_payload_fields(item.model_dump(by_alias=True), fill_missing=True)
    _validate_dependencies(update_data.get("dependencies", []), db)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    try:
        db.commit()
        db.refresh(db_item)
        log_manager.info(f"Successfully updated roadmap item ID: {item_id}")
        return RoadmapItem.model_validate(db_item)
    except Exception as e:
        db.rollback()
        log_manager.error(f"Error updating roadmap item ID {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update roadmap item: {e}")

@router.post("/import-text", response_model=RoadmapItem)
def import_roadmap_item_from_text(payload: RoadmapImportText, db: Session = Depends(get_db)):
    """
    Parses a raw text block to create a new roadmap item.
    """
    log_manager.info("Attempting to import roadmap item from text block.")
    try:
        # Extract the 'text' field from the decoded payload
        text_to_parse = payload.text # Use payload.text directly
        if not text_to_parse:
            raise HTTPException(status_code=400, detail="Request body must contain a 'text' field.")

        parsed_data = parse_roadmap_text(text_to_parse)

        # Validate required fields
        required_fields = ['version', 'codename', 'goal', 'description', 'status']
        for field in required_fields:
            if field not in parsed_data or not parsed_data[field]:
                raise HTTPException(status_code=400, detail=f"Parsing error: Missing required field '{field}'")

        roadmap_item_create = RoadmapItemCreate(**parsed_data)
        payload = _normalize_payload_fields(roadmap_item_create.model_dump(by_alias=True), fill_missing=True)
        _validate_dependencies(payload.get("dependencies", []), db)
        db_item = DBRoadmapItem(**payload)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        log_manager.info(f"Successfully imported and created roadmap item: {db_item.version}")
        return RoadmapItem.model_validate(db_item)

    except HTTPException as he:
        log_manager.error(f"HTTP exception during text import: {he.detail}")
        raise he
    except Exception as e:
        db.rollback()
        log_manager.error(f"Error importing roadmap item from text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import roadmap item from text: {e}")

@router.delete("/{item_id}", response_model=Dict[str, str])
def delete_roadmap_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete a roadmap item by its ID.
    """
    log_manager.info(f"Attempting to delete roadmap item with ID: {item_id}")
    db_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.id == item_id).first()
    if not db_item:
        log_manager.warning(f"Delete failed: Roadmap item with ID {item_id} not found.")
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    try:
        db.delete(db_item)
        db.commit()
        log_manager.info(f"Successfully deleted roadmap item ID: {item_id}")
        return {"message": "Roadmap item deleted successfully"}
    except Exception as e:
        db.rollback()
        log_manager.error(f"Error deleting roadmap item ID {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete roadmap item: {e}")
