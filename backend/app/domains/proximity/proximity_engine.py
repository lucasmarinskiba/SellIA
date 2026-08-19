"""Proximity marketing engine — detect nearby users and trigger automations.

Calculates distance between user location (IP geolocation) and business locations.
Triggers location-based automations when user proximity meets thresholds.
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.businesses.models import Business
from app.domains.businesses.location_models import Location

logger = logging.getLogger(__name__)


@dataclass
class GeoPoint:
    """Geographic coordinate."""
    latitude: float
    longitude: float

    def distance_km_to(self, other: "GeoPoint") -> float:
        """Calculate distance to another point using Haversine formula (km)."""
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance


@dataclass
class ProximityMatch:
    """Result of proximity check."""
    location: Location
    distance_km: float
    is_nearby: bool  # True if within radius


class ProximityEngine:
    """Detect user proximity to business locations and trigger automations."""

    DEFAULT_PROXIMITY_RADIUS_KM = 5.0

    @staticmethod
    def check_proximity(
        user_lat: float,
        user_lng: float,
        business: Business,
        db: Session,
        radius_km: Optional[float] = None
    ) -> list[ProximityMatch]:
        """
        Check if user is near any business location.

        Args:
            user_lat: User latitude
            user_lng: User longitude
            business: Business entity
            db: Database session
            radius_km: Proximity radius (default: 5km). If None, uses location-specific service_radius_km

        Returns:
            List of ProximityMatch, sorted by distance (closest first)
        """
        user_point = GeoPoint(user_lat, user_lng)

        # Get all active locations
        locations = db.query(Location).filter(
            Location.business_id == business.id,
            Location.is_active == True
        ).all()

        matches = []

        for location in locations:
            loc_point = GeoPoint(location.latitude, location.longitude)
            distance = user_point.distance_km_to(loc_point)

            # Use location-specific radius or default
            threshold = radius_km or location.service_radius_km or ProximityEngine.DEFAULT_PROXIMITY_RADIUS_KM

            is_nearby = distance <= threshold

            matches.append(ProximityMatch(
                location=location,
                distance_km=distance,
                is_nearby=is_nearby
            ))

        # Sort by distance
        matches.sort(key=lambda m: m.distance_km)

        return matches

    @staticmethod
    def find_nearest_location(
        user_lat: float,
        user_lng: float,
        business: Business,
        db: Session
    ) -> Optional[ProximityMatch]:
        """Get closest location to user, regardless of proximity threshold."""
        matches = ProximityEngine.check_proximity(user_lat, user_lng, business, db)
        return matches[0] if matches else None

    @staticmethod
    def get_locations_within_radius(
        user_lat: float,
        user_lng: float,
        business: Business,
        radius_km: float,
        db: Session
    ) -> list[Location]:
        """Get all locations within specified radius."""
        matches = ProximityEngine.check_proximity(user_lat, user_lng, business, db, radius_km)
        return [m.location for m in matches if m.is_nearby]

    @staticmethod
    def should_trigger_proximity_automation(
        user_lat: float,
        user_lng: float,
        location: Location
    ) -> bool:
        """Check if user-location distance warrants automation trigger."""
        user_point = GeoPoint(user_lat, user_lng)
        loc_point = GeoPoint(location.latitude, location.longitude)
        distance = user_point.distance_km_to(loc_point)

        threshold = location.service_radius_km or ProximityEngine.DEFAULT_PROXIMITY_RADIUS_KM

        return distance <= threshold

    @staticmethod
    def estimate_eta_minutes(
        user_lat: float,
        user_lng: float,
        location: Location,
        avg_speed_kmh: float = 40
    ) -> int:
        """Estimate time to reach location (minutes)."""
        user_point = GeoPoint(user_lat, user_lng)
        loc_point = GeoPoint(location.latitude, location.longitude)
        distance = user_point.distance_km_to(loc_point)

        # distance / speed = time_hours; * 60 = time_minutes
        minutes = int((distance / avg_speed_kmh) * 60)

        return max(1, minutes)  # At least 1 minute


class ProximityTriggerConfig:
    """Configuration for proximity-based automation triggers."""

    # Trigger names (should match automation engine trigger names)
    PROXIMITY_CHECK_NEARBY = "proximity_check_nearby"
    QR_SCANNED_AT_LOCATION = "qr_scanned_at_location"
    LOCATION_VISIT_DETECTED = "location_visit_detected"
    QUALIFIED_LEAD_NEARBY = "qualified_lead_nearby"
    TRIAL_USER_NEARBY = "trial_user_nearby"
    SERVICE_INQUIRY_NEARBY = "service_inquiry_nearby"

    @staticmethod
    def get_trigger_for_strategy(strategy: str) -> Optional[str]:
        """Map localization strategy to trigger name."""
        triggers = {
            "QR_INVITE": ProximityTriggerConfig.PROXIMITY_CHECK_NEARBY,
            "FOOT_TRAFFIC": ProximityTriggerConfig.LOCATION_VISIT_DETECTED,
            "TOUR_SCHEDULING": ProximityTriggerConfig.QUALIFIED_LEAD_NEARBY,
            "DEMO_BOOKING": ProximityTriggerConfig.TRIAL_USER_NEARBY,
            "SERVICE_DISPATCH": ProximityTriggerConfig.SERVICE_INQUIRY_NEARBY,
        }
        return triggers.get(strategy)

    @staticmethod
    def default_config_for_trigger(trigger_name: str) -> dict:
        """Get default automation config per trigger."""
        defaults = {
            ProximityTriggerConfig.PROXIMITY_CHECK_NEARBY: {
                "radius_km": 5.0,
                "trigger_once_per_day": True,
                "require_lead_score_min": 50,
                "send_via": ["sms", "email"],
            },
            ProximityTriggerConfig.LOCATION_VISIT_DETECTED: {
                "radius_km": 0.5,  # ~500m walk
                "dwell_threshold_minutes": 5,
                "send_via": ["sms"],
            },
            ProximityTriggerConfig.QUALIFIED_LEAD_NEARBY: {
                "radius_km": 50.0,
                "require_lead_score_min": 70,
                "days_advance_notice": 3,
                "send_via": ["email"],
            },
            ProximityTriggerConfig.TRIAL_USER_NEARBY: {
                "radius_km": 10.0,
                "require_trial_active": True,
                "send_via": ["email", "sms"],
            },
            ProximityTriggerConfig.SERVICE_INQUIRY_NEARBY: {
                "radius_km": 30.0,
                "days_to_appointment": 7,
                "send_via": ["sms"],
            },
        }
        return defaults.get(trigger_name, {})
