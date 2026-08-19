"""Mobile geofence API — auto check-in + nearby locations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.users.models import User
from app.domains.locations.geofence_service import GeofenceTriggerService
from app.domains.locations.models import Location

router = APIRouter(prefix="/api/v1/mobile", tags=["mobile-geofence"])


class GeolocationPayload(BaseModel):
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None


class GeofenceCheckRequest(BaseModel):
    latitude: float
    longitude: float
    business_id: UUID
    accuracy_meters: Optional[float] = None


@router.post("/geofence/check")
async def check_geofence(
    request: GeofenceCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Check if user in geofence. Auto check-in if enabled.

    Mobile app calls this periodically (every 30-60s when app in foreground).
    """
    try:
        # Get user's business locations
        from app.domains.businesses.models import Business

        business = db.query(Business).filter(Business.id == request.business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        # Get location records (assuming locations stored in Location table)
        locations = db.query(Location).filter(Location.business_id == request.business_id).all()

        result = GeofenceTriggerService.check_geofence_triggers(
            user_id=current_user.id,
            user_lat=request.latitude,
            user_lng=request.longitude,
            business_id=request.business_id,
            locations=locations,
            db=db
        )

        return {
            "triggered": result.get("triggered", False),
            "location_id": result.get("location_id"),
            "location_name": result.get("location_name"),
            "checkin_id": result.get("checkin_id"),
            "distance_km": result.get("distance_km"),
            "message": result.get("message"),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/nearby")
async def get_nearby_locations(
    request: GeofenceCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List locations within 500m radius."""
    try:
        locations = db.query(Location).filter(Location.business_id == request.business_id).all()

        nearby = GeofenceTriggerService.get_nearby_locations(
            user_lat=request.latitude,
            user_lng=request.longitude,
            business_id=request.business_id,
            locations=locations,
            radius_km=0.5
        )

        return {
            "user_location": {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "accuracy_meters": request.accuracy_meters
            },
            "nearby_locations": nearby,
            "count": len(nearby)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/geofence/subscribe")
async def subscribe_to_geofence(
    business_id: UUID,
    radius_km: float = 0.5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Enable background geofence monitoring (iOS/Android).

    Returns push notification settings for mobile app to register with OS.
    """
    try:
        # Get business locations for geofence setup
        locations = db.query(Location).filter(Location.business_id == business_id).all()

        geofences = []
        for loc in locations:
            geofences.append({
                "id": str(loc.id),
                "name": loc.name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "radius_meters": int(radius_km * 1000),
                "trigger_on_enter": True,
                "trigger_on_exit": False
            })

        return {
            "subscription_active": True,
            "business_id": str(business_id),
            "geofences": geofences,
            "polling_interval_seconds": 30,
            "background_enabled": True,
            "note": "iOS requires location permission 'Always'. Android requires 'Allow all the time'."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
