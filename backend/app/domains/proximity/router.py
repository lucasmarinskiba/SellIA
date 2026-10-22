"""Phase 5B: Proximity Detection Endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.proximity.engine import ProximityEngine

router = APIRouter(prefix="/api/v1/proximity", tags=["proximity"])


@router.post("/check-nearby")
async def check_nearby_locations(
    business_id: UUID,
    user_lat: float,
    user_lon: float,
    db: Annotated[Session, Depends(get_db)],
    user_id: UUID | None = None,
) -> dict:
    nearby = await ProximityEngine.check_proximity_to_locations(
        db, business_id, user_lat, user_lon
    )
    result = []
    for location, distance in nearby:
        if user_id:
            await ProximityEngine.trigger_proximity_automation(
                db, business_id, user_id, location, distance
            )
        result.append(
            {
                "location_id": location.id,
                "location_name": location.location_name,
                "distance_km": round(distance, 2),
                "address": location.address,
            }
        )
    return {"nearby_locations": result, "count": len(result)}


@router.get("/location-nearby-users")
async def get_nearby_users(
    business_id: UUID,
    location_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    max_distance_km: float = 5,
) -> dict:
    users = await ProximityEngine.get_nearby_users(
        db, business_id, location_id, max_distance_km
    )
    return {"location_id": location_id, "nearby_users": users, "count": len(users)}


@router.get("/user-proximity-history")
async def get_user_proximity_history(
    business_id: UUID,
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    history = await ProximityEngine.get_proximity_history(db, business_id, user_id)
    return {
        "user_id": user_id,
        "proximity_events": history,
        "total_events": len(history),
    }
