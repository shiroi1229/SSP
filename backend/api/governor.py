from fastapi import APIRouter, Request
import logging

router = APIRouter(prefix="/api")

@router.post("/governor/ui_error")
async def ui_error_report(request: Request):
    payload = await request.json()
    logging.info(f"Received UI error report: {payload}")
    print(f"Received UI error report: {payload}") # For immediate visibility in CLI
    return {"status": "received"}