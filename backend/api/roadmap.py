from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json
import os

router = APIRouter(prefix="/api")

@router.get("/roadmap/current")
async def get_current_roadmap():
    """
    Returns the current roadmap data from cache or extended roadmap file.
    """
    cache_path = "data/system_roadmap_cache.json"
    extended_roadmap_path = "docs/roadmap/system_roadmap_extended.json"

    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        elif os.path.exists(extended_roadmap_path):
            with open(extended_roadmap_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        else:
            raise HTTPException(status_code=404, detail="Roadmap data not found.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding roadmap JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
