# path: query_v08.py
# version: v0.1
# purpose: Dump roadmap items around v0.8 for quick inspection

# -*- coding: utf-8 -*-
import json

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem

session = SessionLocal()
try:
   rows = (
      session.query(RoadmapItem)
      .filter(RoadmapItem.version.in_(["v0.8", "v0.8.1", "v0.8.1_PoC"]))
      .all()
   )
   print(
      json.dumps(
         [
            {
               "version": r.version,
               "codename": r.codename,
               "goal": r.goal,
               "status": r.status,
               "progress": r.progress,
               "owner": r.owner,
               "description": r.description,
               "development_details": r.development_details,
            }
            for r in rows
         ],
         ensure_ascii=False,
         indent=2,
      )
   )
finally:
   session.close()
