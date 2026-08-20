"""Phase 5A: Location Management Service."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domains.locations.models import LocationProfile, BusinessModel, ProximityEvent, OfflineConversion, LocationVisit


class LocationService:
    @staticmethod
    def create_location(
        db: Session,
        business_id: UUID,
        location_name: str,
        address: str,
        latitude: float,
        longitude: float,
        location_type: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        hours_json: Optional[dict] = None,
        capacity: int = 0,
        geofence_radius_km: float = 5,
    ) -> LocationProfile:
        loc = LocationProfile(
            business_id=business_id,
            location_name=location_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            location_type=location_type,
            phone=phone,
            email=email,
            hours_json=hours_json,
            capacity=capacity,
            geofence_radius_km=geofence_radius_km,
        )
        db.add(loc)
        db.commit()
        db.refresh(loc)
        return loc

    @staticmethod
    def list_locations(db: Session, business_id: UUID) -> List[LocationProfile]:
        return db.query(LocationProfile).filter(LocationProfile.business_id == business_id).all()

    @staticmethod
    def detect_business_model(db: Session, business_id: UUID) -> BusinessModel:
        locations = db.query(LocationProfile).filter(LocationProfile.business_id == business_id).all()
        locations_count = len(locations)
        has_physical_location = locations_count > 0

        # Detect online presence (from existing online channels)
        has_online_presence = True  # Assume all SellIA users have online presence

        if locations_count == 0:
            model_class = "ONLINE_ONLY"
            confidence = 1.0
        elif locations_count >= 3:
            model_class = "OFFLINE_FIRST"
            confidence = 0.95
        elif has_online_presence and has_physical_location:
            if locations_count == 1:
                model_class = "HYBRID_LIGHT"
                confidence = 0.8
            else:
                model_class = "HYBRID_HEAVY"
                confidence = 0.85
        else:
            model_class = "HYBRID_LIGHT"
            confidence = 0.7

        existing = db.query(BusinessModel).filter(BusinessModel.business_id == business_id).first()
        if existing:
            existing.model_class = model_class
            existing.model_confidence = confidence
            existing.locations_count = locations_count
            existing.has_online_presence = has_online_presence
            existing.has_physical_location = has_physical_location
            db.commit()
            db.refresh(existing)
            return existing

        model = BusinessModel(
            business_id=business_id,
            model_class=model_class,
            model_confidence=confidence,
            locations_count=locations_count,
            has_online_presence=has_online_presence,
            has_physical_location=has_physical_location,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def log_offline_conversion(
        db: Session,
        business_id: UUID,
        location_id: UUID,
        visit_type: str,
        user_id: Optional[UUID] = None,
        entry_method: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> OfflineConversion:
        conversion = OfflineConversion(
            business_id=business_id,
            location_id=location_id,
            user_id=user_id,
            visit_type=visit_type,
            entry_method=entry_method,
            phone=phone,
            email=email,
            notes=notes,
            entry_time=datetime.now(timezone.utc),
        )
        db.add(conversion)
        db.commit()
        db.refresh(conversion)
        return conversion

    @staticmethod
    def log_location_visit(
        db: Session,
        business_id: UUID,
        location_id: UUID,
        user_id: UUID,
        entry_channel: Optional[str] = None,
    ) -> LocationVisit:
        visit = LocationVisit(
            business_id=business_id,
            location_id=location_id,
            user_id=user_id,
            entry_time=datetime.now(timezone.utc),
            entry_channel=entry_channel,
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def end_location_visit(db: Session, visit_id: UUID) -> LocationVisit:
        visit = db.query(LocationVisit).filter(LocationVisit.id == visit_id).first()
        if visit:
            visit.exit_time = datetime.now(timezone.utc)
            if visit.entry_time:
                delta = visit.exit_time - visit.entry_time
                visit.dwell_minutes = int(delta.total_seconds() / 60)
            db.commit()
            db.refresh(visit)
        return visit

    @staticmethod
    def log_proximity_event(
        db: Session,
        business_id: UUID,
        user_id: UUID,
        location_id: UUID,
        distance_km: float,
    ) -> ProximityEvent:
        event = ProximityEvent(
            business_id=business_id,
            user_id=user_id,
            location_id=location_id,
            distance_km=distance_km,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_location_metrics(db: Session, business_id: UUID, location_id: UUID) -> dict:
        visits = db.query(LocationVisit).filter(
            and_(LocationVisit.business_id == business_id, LocationVisit.location_id == location_id)
        ).all()

        total_visits = len(visits)
        total_dwell_minutes = sum(v.dwell_minutes for v in visits)
        avg_dwell = total_dwell_minutes / total_visits if total_visits > 0 else 0
        purchase_visits = sum(1 for v in visits if v.purchase_made)
        conversion_rate = (purchase_visits / total_visits * 100) if total_visits > 0 else 0
        total_purchase_value = sum(v.purchase_value for v in visits)

        return {
            "total_visits": total_visits,
            "avg_dwell_minutes": avg_dwell,
            "purchase_visits": purchase_visits,
            "conversion_rate": conversion_rate,
            "total_purchase_value": total_purchase_value,
        }
