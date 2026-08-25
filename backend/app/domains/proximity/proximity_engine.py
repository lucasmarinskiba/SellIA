"""Proximity marketing engine for location-based automations."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Location with coordinates."""
    location_id: UUID
    latitude: float
    longitude: float
    name: str
    radius_km: float = 5.0


@dataclass
class UserLocation:
    """User's detected location."""
    user_id: UUID
    latitude: float
    longitude: float
    confidence: str = "ip"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class ProximityEvent:
    """Event when user enters location geofence."""
    event_id: str
    user_id: UUID
    location_id: UUID
    distance_km: float
    detected_at: datetime
    automation_triggered: bool = False
    automation_id: Optional[UUID] = None


class ProximityEngine:
    """Detects proximity & triggers automations."""

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between coordinates in km."""
        R = 6371
        φ1 = math.radians(lat1)
        φ2 = math.radians(lat2)
        Δφ = math.radians(lat2 - lat1)
        Δλ = math.radians(lon2 - lon1)

        a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    @staticmethod
    def check_proximity(
        user_location: UserLocation,
        locations: List[Location],
    ) -> List[ProximityEvent]:
        """Check if user near any location."""
        nearby = []
        for loc in locations:
            distance = ProximityEngine.haversine_distance(
                user_location.latitude,
                user_location.longitude,
                loc.latitude,
                loc.longitude
            )
            radius = loc.radius_km or 5.0
            if distance <= radius:
                event = ProximityEvent(
                    event_id=f"prox_{user_location.user_id}_{loc.location_id}",
                    user_id=user_location.user_id,
                    location_id=loc.location_id,
                    distance_km=round(distance, 2),
                    detected_at=user_location.timestamp
                )
                nearby.append(event)
        return nearby
