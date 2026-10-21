"""Geofence trigger service — auto check-in on proximity."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.locations.checkin_models import CheckinType
from app.domains.locations.checkin_service import LocationCheckinService
from app.domains.proximity.proximity_engine import ProximityEngine

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
        db: Session | None = None
    ) -> dict:
        """Check if user near any location. Auto check-in if enabled.

        Returns: {triggered: bool, location_id: UUID, checkin_id: UUID, message: str}
        """
        if not db or not locations:
            return {"triggered": False}

        # Find nearest location within radius
        for loc in locations:
            distance_km = ProximityEngine.haversine_distance(
                user_lat, user_lng, loc.latitude, loc.longitude
            )

            if distance_km <= GeofenceTriggerService.DEFAULT_RADIUS_KM:
                # Check if user already checked in recently (avoid duplicates)
                recent_checkin = db.query(LocationCheckin).filter(
                    LocationCheckin.location_id == loc.id,
                    LocationCheckin.user_id == user_id,
                    LocationCheckin.checkin_time >= datetime.now(UTC) - timedelta(minutes=5)
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
                    logger.exception("Geofence auto check-in failed")
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
        nearby = []
        for loc in locations:
            distance_km = ProximityEngine.haversine_distance(
                user_lat, user_lng, loc.latitude, loc.longitude
            )

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
