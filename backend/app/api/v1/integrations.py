"""Integration marketplace API."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["integrations"])

@router.get("/apps")
def list_apps():
    return {"apps": []}

@router.post("/businesses/{business_id}/connections")
def create_connection(business_id):
    return {"status": "ok"}
