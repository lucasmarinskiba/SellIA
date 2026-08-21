"""Phase 5B: Proximity Engine & Geofence Detection."""
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.domains.locations.models import LocationProfile, ProximityEvent
from app.domains.locations.service import LocationService


class ProximityEngine:
    """Calculate distances and detect proximity events using Haversine formula."""

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two lat/lon points."""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        return c * r

    @staticmethod
    async def check_proximity_to_locations(
        db: AsyncSession,
        business_id: UUID,
        user_lat: float,
        user_lon: float,
    ) -> List[Tuple[LocationProfile, float]]:
        result = await db.execute(
            select(LocationProfile).where(
                and_(
                    LocationProfile.business_id == business_id,
                    LocationProfile.is_active == True,
                )
            )
        )
        locations = result.scalars().all()
        nearby = []
        for loc in locations:
            distance = ProximityEngine.haversine_distance(user_lat, user_lon, loc.latitude, loc.longitude)
            if distance <= loc.geofence_radius_km:
                nearby.append((loc, distance))
        return nearby

    @staticmethod
    async def trigger_proximity_automation(
        db,
        business_id: UUID,
        user_id: UUID,
        location: LocationProfile,
        distance_km: float,
    ) -> Optional[ProximityEvent]:
        event = await LocationService.log_proximity_event(db, business_id, user_id, location.id, distance_km)
        return event

    @staticmethod
    async def get_nearby_users(
        db,
        business_id: UUID,
        location_id: UUID,
        max_distance_km: float = 5,
    ) -> List[dict]:
        from sqlalchemy import select
        result = await db.execute(
            select(ProximityEvent).where(
                and_(
                    ProximityEvent.business_id == business_id,
                    ProximityEvent.location_id == location_id,
                    ProximityEvent.distance_km <= max_distance_km,
                )
            ).order_by(ProximityEvent.created_at.desc())
        )
        events = result.scalars().all()
        return [{"user_id": e.user_id, "distance_km": e.distance_km, "detected_at": e.created_at} for e in events]

    @staticmethod
    async def get_proximity_history(
        db,
        business_id: UUID,
        user_id: UUID,
    ) -> List[dict]:
        from sqlalchemy import select
        result = await db.execute(
            select(ProximityEvent).where(
                and_(
                    ProximityEvent.business_id == business_id,
                    ProximityEvent.user_id == user_id,
                )
            ).order_by(ProximityEvent.created_at.desc())
        )
        events = result.scalars().all()
        return [{"location_id": e.location_id, "distance_km": e.distance_km, "event_type": e.event_type, "detected_at": e.created_at} for e in events]
