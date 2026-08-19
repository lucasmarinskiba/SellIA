"""Geofence trigger service — auto check-in on proximity."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from app.domains.locations.proximity_engine import ProximityEngine, GeoPoint
from app.domains.locations.checkin_service import LocationCheckinService
from app.domains.locations.checkin_models import CheckinType

logger = logging.getLogger(__name__)


class GeofenceTriggerService:
    """Auto-trigger check-in when user enters location radius."""

    DEFAULT_RADIUS_KM = 0.5  # 500m

    @staticmethod
    def check_geofence_triggers(
        user_id: UUID,
        user_lat: float,
        user_lng: float,
        business_id: UUID,
        locations: list,  # List of Location objects with lat/lng
        db: Optional[Session] = None
    ) -> dict:
        """Check if user near any location. Auto check-in if enabled.

        Returns: {triggered: bool, location_id: UUID, checkin_id: UUID, message: str}
        """
        if not db or not locations:
            return {"triggered": False}

        user_point = GeoPoint(lat=user_lat, lng=user_lng)
        engine = ProximityEngine()

        # Find nearest location within radius
        for loc in locations:
            loc_point = GeoPoint(lat=loc.latitude, lng=loc.longitude)
            distance_km = engine.haversine_distance(user_point, loc_point)

            if distance_km <= GeofenceTriggerService.DEFAULT_RADIUS_KM:
                # Check if user already checked in recently (avoid duplicates)
                recent_checkin = db.query(LocationCheckin).filter(
                    LocationCheckin.location_id == loc.id,
                    LocationCheckin.user_id == user_id,
                    LocationCheckin.checkin_time >= datetime.now(timezone.utc) - timedelta(minutes=5)
                ).first()

                if recent_checkin:
                    return {
                        "triggered": False,
                        "reason": "Already checked in within 5 minutes"
                    }

                # Auto check-in via geofence
                try:
                    checkin = LocationCheckinService.checkin_visitor(
                        location_id=loc.id,
                        business_id=business_id,
                        checkin_type=CheckinType.GEOFENCE,
                        user_id=user_id,
                        db=db
                    )

                    logger.info(f"Geofence trigger: user {user_id} auto checked in to {loc.id}")

                    return {
                        "triggered": True,
                        "location_id": str(loc.id),
                        "location_name": loc.name,
                        "checkin_id": str(checkin.id),
                        "distance_km": round(distance_km, 2),
                        "message": f"Welcome to {loc.name}!"
                    }
                except Exception as e:
                    logger.error(f"Geofence auto check-in failed: {e}")
                    return {"triggered": False, "error": str(e)}

        return {"triggered": False, "reason": "No locations in range"}

    @staticmethod
    def get_nearby_locations(
        user_lat: float,
        user_lng: float,
        business_id: UUID,
        locations: list,
        radius_km: float = DEFAULT_RADIUS_KM
    ) -> list:
        """List all locations within radius."""
        user_point = GeoPoint(lat=user_lat, lng=user_lng)
        engine = ProximityEngine()

        nearby = []
        for loc in locations:
            loc_point = GeoPoint(lat=loc.latitude, lng=loc.longitude)
            distance_km = engine.haversine_distance(user_point, loc_point)

            if distance_km <= radius_km:
                nearby.append({
                    "location_id": str(loc.id),
                    "name": loc.name,
                    "distance_km": round(distance_km, 2),
                    "address": loc.address,
                    "hours": loc.hours_json,
                    "is_open_now": True  # TODO: compare with hours_json
                })

        return sorted(nearby, key=lambda x: x["distance_km"])


# Import here to avoid circular imports
from app.domains.locations.checkin_models import LocationCheckin
