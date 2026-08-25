"""Phase 5B: Proximity tracking & offline conversion logging."""

import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proximity", tags=["proximity"])


class OfflineConversionLog(BaseModel):
    """Log offline visit/conversion."""
    location_id: UUID
    latitude: float
    longitude: float
    visit_type: str = "visit"  # visit, demo, pickup, service
    notes: Optional[str] = None


class ProximityCheckRequest(BaseModel):
    """Check if user near any location."""
    latitude: float
    longitude: float


@router.post("/check-nearby")
async def check_proximity(
    req: ProximityCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user near any business location."""
    # TODO: Get user's businesses + locations from DB
    # For now: return empty list (Phase 5B foundation)
    return {
        "user_id": str(current_user.id),
        "latitude": req.latitude,
        "longitude": req.longitude,
        "nearby_locations": [],
        "message": "No locations within 5km"
    }


@router.post("/log-visit")
async def log_offline_conversion(
    conversion: OfflineConversionLog,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log location visit or offline conversion."""
    # TODO: Create offline_conversions table entry
    return {
        "status": "logged",
        "location_id": str(conversion.location_id),
        "visit_type": conversion.visit_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/nearby-users/{location_id}")
async def get_nearby_users(
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get users near a location (for business owner)."""
    # TODO: Query users near location, return list
    return {
        "location_id": str(location_id),
        "nearby_users": [],
        "total": 0
    }
