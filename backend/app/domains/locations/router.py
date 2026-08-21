"""Phase 5A: Location Endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.domains.locations.service import LocationService
from app.domains.locations.models import LocationProfile, BusinessModel


router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


class LocationCreateRequest(BaseModel):
    location_name: str
    address: str
    latitude: float
    longitude: float
    location_type: str
    phone: Optional[str] = None
    email: Optional[str] = None
    hours_json: Optional[dict] = None
    capacity: int = 0
    geofence_radius_km: float = 5


class LocationResponse(BaseModel):
    id: UUID
    business_id: UUID
    location_name: str
    address: str
    latitude: float
    longitude: float
    location_type: str
    phone: Optional[str]
    email: Optional[str]
    capacity: int
    geofence_radius_km: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BusinessModelResponse(BaseModel):
    id: UUID
    business_id: UUID
    model_class: str
    model_confidence: float
    locations_count: int
    has_online_presence: bool
    has_physical_location: bool

    class Config:
        from_attributes = True


@router.post("/create")
async def create_location(
    business_id: UUID,
    req: LocationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    loc = await LocationService.create_location(
        db=db,
        business_id=business_id,
        location_name=req.location_name,
        address=req.address,
        latitude=req.latitude,
        longitude=req.longitude,
        location_type=req.location_type,
        phone=req.phone,
        email=req.email,
        hours_json=req.hours_json,
        capacity=req.capacity,
        geofence_radius_km=req.geofence_radius_km,
    )
    return LocationResponse.from_orm(loc)


@router.get("/list")
async def list_locations(business_id: UUID, db: AsyncSession = Depends(get_db)) -> List[LocationResponse]:
    locs = await LocationService.list_locations(db, business_id)
    return [LocationResponse.from_orm(loc) for loc in locs]


@router.get("/metrics")
async def location_metrics(
    business_id: UUID,
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    metrics = await LocationService.get_location_metrics(db, business_id, location_id)
    return metrics


@router.post("/detect-model")
async def detect_business_model(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BusinessModelResponse:
    model = await LocationService.detect_business_model(db, business_id)
    return BusinessModelResponse.from_orm(model)


@router.post("/offline-conversion")
def log_offline_conversion(
    business_id: UUID,
    location_id: UUID,
    visit_type: str,
    user_id: Optional[UUID] = None,
    entry_method: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    conversion = LocationService.log_offline_conversion(
        db=db,
        business_id=business_id,
        location_id=location_id,
        visit_type=visit_type,
        user_id=user_id,
        entry_method=entry_method,
        phone=phone,
        email=email,
        notes=notes,
    )
    return {"id": conversion.id, "message": "Offline conversion logged"}


@router.post("/visit-log")
def log_visit(
    business_id: UUID,
    location_id: UUID,
    user_id: UUID,
    entry_channel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    visit = LocationService.log_location_visit(
        db=db,
        business_id=business_id,
        location_id=location_id,
        user_id=user_id,
        entry_channel=entry_channel,
    )
    return {"id": visit.id, "message": "Visit logged"}


@router.post("/visit-end")
def end_visit(
    visit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    visit = LocationService.end_location_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"id": visit.id, "dwell_minutes": visit.dwell_minutes, "message": "Visit ended"}
