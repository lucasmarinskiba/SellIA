"""Service layer for offline conversion tracking and analytics."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.domains.analytics.offline_models import (
    OfflineConversion, GeoProximityEvent, LocationVisitMetric,
    VisitType, DemographicSource
)
from app.domains.businesses.location_models import Location
from app.domains.proximity.proximity_engine import ProximityEngine

logger = logging.getLogger(__name__)


class OfflineAnalyticsService:
    """Service for logging and analyzing offline conversions."""

    @staticmethod
    def log_visit(
        business_id: UUID,
        location_id: UUID,
        visit_type: VisitType,
        visitor_phone: Optional[str] = None,
        visitor_email: Optional[str] = None,
        visitor_name: Optional[str] = None,
        visitor_latitude: Optional[float] = None,
        visitor_longitude: Optional[float] = None,
        visitor_ip: Optional[str] = None,
        demographic_source: Optional[DemographicSource] = None,
        confidence_score: float = 0.5,
        conversation_id: Optional[UUID] = None,
        purchased: bool = False,
        purchase_amount: Optional[Decimal] = None,
        staff_notes: Optional[str] = None,
        db: Optional[Session] = None
    ) -> OfflineConversion:
        """
        Log a visitor to a physical location.

        Args:
            business_id: Business owner
            location_id: Physical location visited
            visit_type: Type of visit (walk_in, qr_scan, scheduled_demo, etc)
            visitor_*: Visitor identification info
            demographic_source: How visitor was identified
            confidence_score: 0-1.0 confidence this is the correct visitor
            conversation_id: Link to online conversation (if matched)
            purchased: Whether purchase made during visit
            purchase_amount: Transaction amount
            staff_notes: Staff notes about the visit
            db: Database session

        Returns:
            OfflineConversion record
        """
        if not db:
            raise ValueError("Database session required")

        conversion = OfflineConversion(
            business_id=business_id,
            location_id=location_id,
            visit_type=visit_type,
            visitor_phone=visitor_phone,
            visitor_email=visitor_email,
            visitor_name=visitor_name,
            visitor_latitude=visitor_latitude,
            visitor_longitude=visitor_longitude,
            visitor_ip_address=visitor_ip,
            demographic_source=demographic_source,
            confidence_score=confidence_score,
            conversation_id=conversation_id,
            purchased=purchased,
            purchase_amount=purchase_amount,
            staff_notes=staff_notes,
        )

        db.add(conversion)
        db.commit()
        db.refresh(conversion)

        logger.info(f"Logged offline visit: {conversion.id} at {location_id} ({visit_type})")

        return conversion

    @staticmethod
    def log_proximity_event(
        business_id: UUID,
        location_id: UUID,
        conversation_id: UUID,
        user_latitude: float,
        user_longitude: float,
        distance_km: float,
        trigger_name: str,
        visitor_phone: Optional[str] = None,
        visitor_email: Optional[str] = None,
        automation_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> GeoProximityEvent:
        """
        Log proximity trigger event for user near location.

        Args:
            business_id: Business owner
            location_id: Location triggered
            conversation_id: User conversation
            user_latitude: User's latitude at time of trigger
            user_longitude: User's longitude at time of trigger
            distance_km: Distance from user to location
            trigger_name: Automation trigger name (e.g., "proximity_check_nearby")
            visitor_phone: Visitor phone (optional)
            visitor_email: Visitor email (optional)
            automation_id: Automation that will be triggered
            db: Database session

        Returns:
            GeoProximityEvent record
        """
        if not db:
            raise ValueError("Database session required")

        event = GeoProximityEvent(
            business_id=business_id,
            location_id=location_id,
            conversation_id=conversation_id,
            visitor_phone=visitor_phone,
            visitor_email=visitor_email,
            user_latitude=user_latitude,
            user_longitude=user_longitude,
            distance_km=distance_km,
            trigger_name=trigger_name,
            automation_id=automation_id,
            automation_triggered=False,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(f"Logged proximity event: {trigger_name} at {location_id} ({distance_km:.1f}km)")

        return event

    @staticmethod
    def mark_proximity_executed(
        proximity_event_id: UUID,
        db: Optional[Session] = None
    ) -> GeoProximityEvent:
        """Mark proximity event as having triggered automation."""
        if not db:
            raise ValueError("Database session required")

        event = db.query(GeoProximityEvent).filter(
            GeoProximityEvent.id == proximity_event_id
        ).first()

        if event:
            event.automation_triggered = True
            event.automation_executed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(event)

        return event

    @staticmethod
    def end_visit(
        conversion_id: UUID,
        purchased: bool = False,
        purchase_amount: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> OfflineConversion:
        """Mark end of visit and calculate dwell time."""
        if not db:
            raise ValueError("Database session required")

        conversion = db.query(OfflineConversion).filter(
            OfflineConversion.id == conversion_id
        ).first()

        if not conversion:
            raise ValueError(f"Conversion {conversion_id} not found")

        conversion.exit_time = datetime.now(timezone.utc)

        # Calculate dwell time
        if conversion.entry_time and conversion.exit_time:
            delta = conversion.exit_time - conversion.entry_time
            conversion.dwell_minutes = int(delta.total_seconds() / 60)

        # Update purchase info
        if purchased:
            conversion.purchased = True
            conversion.purchase_amount = purchase_amount

        db.commit()
        db.refresh(conversion)

        logger.info(f"Ended visit {conversion_id}: {conversion.dwell_minutes}min, purchased={purchased}")

        return conversion

    @staticmethod
    def get_daily_metrics(
        location_id: UUID,
        date: str,  # YYYY-MM-DD
        db: Optional[Session] = None
    ) -> Optional[LocationVisitMetric]:
        """Get or create daily metrics for location."""
        if not db:
            raise ValueError("Database session required")

        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return None

        metric = db.query(LocationVisitMetric).filter(
            and_(
                LocationVisitMetric.location_id == location_id,
                LocationVisitMetric.metric_date == date
            )
        ).first()

        if not metric:
            metric = LocationVisitMetric(
                business_id=location.business_id,
                location_id=location_id,
                metric_date=date,
            )
            db.add(metric)
            db.commit()
            db.refresh(metric)

        return metric

    @staticmethod
    def update_daily_metrics(location_id: UUID, date: str, db: Optional[Session] = None) -> None:
        """Recalculate daily metrics from offline_conversions for given date."""
        if not db:
            raise ValueError("Database session required")

        metric = OfflineAnalyticsService.get_daily_metrics(location_id, date, db)
        if not metric:
            return

        # Query visits for the day
        day_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        visits = db.query(OfflineConversion).filter(
            and_(
                OfflineConversion.location_id == location_id,
                OfflineConversion.entry_time >= day_start,
                OfflineConversion.entry_time < day_end
            )
        ).all()

        metric.total_visits = len(visits)
        metric.walk_in_visits = len([v for v in visits if v.visit_type == VisitType.WALK_IN])
        metric.qr_scans = len([v for v in visits if v.visit_type == VisitType.QR_SCAN])
        metric.scheduled_visits = len([v for v in visits if v.visit_type in (
            VisitType.SCHEDULED_DEMO, VisitType.SCHEDULED_TOUR, VisitType.SCHEDULED_APPOINTMENT
        )])

        # Conversion metrics
        converted = [v for v in visits if v.purchased]
        metric.visitors_converted = len(converted)
        metric.total_purchase_value = sum(v.purchase_amount or 0 for v in converted)
        if converted:
            metric.avg_purchase_value = metric.total_purchase_value / len(converted)

        # Engagement metrics
        dwell_times = [v.dwell_minutes for v in visits if v.dwell_minutes]
        if dwell_times:
            metric.avg_dwell_minutes = int(sum(dwell_times) / len(dwell_times))

        contact_collected = len([v for v in visits if v.contact_collected])
        if visits:
            metric.contact_collection_rate = Decimal(contact_collected) / Decimal(len(visits))

        # Hourly breakdown
        hourly_visits = {}
        for v in visits:
            hour = str(v.entry_time.hour).zfill(2)
            hourly_visits[hour] = hourly_visits.get(hour, 0) + 1
        metric.hourly_visits_json = hourly_visits

        db.commit()

        logger.info(f"Updated daily metrics for {location_id} on {date}: {metric.total_visits} visits")

    @staticmethod
    def get_foot_traffic_heatmap(
        location_id: UUID,
        days: int = 30,
        db: Optional[Session] = None
    ) -> dict:
        """Get hourly foot traffic heatmap for last N days."""
        if not db:
            raise ValueError("Database session required")

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        metrics = db.query(LocationVisitMetric).filter(
            and_(
                LocationVisitMetric.location_id == location_id,
                LocationVisitMetric.metric_date >= start_date.strftime("%Y-%m-%d")
            )
        ).all()

        # Aggregate hourly data
        hourly_totals = {}
        for metric in metrics:
            for hour, count in metric.hourly_visits_json.items():
                hourly_totals[hour] = hourly_totals.get(hour, 0) + count

        return {
            "location_id": str(location_id),
            "period_days": days,
            "hourly_heatmap": hourly_totals,
        }

    @staticmethod
    def get_conversion_funnel(
        business_id: UUID,
        days: int = 30,
        db: Optional[Session] = None
    ) -> dict:
        """Get online→offline→purchase conversion funnel for business."""
        if not db:
            raise ValueError("Database session required")

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # All offline conversions in period
        all_conversions = db.query(OfflineConversion).filter(
            and_(
                OfflineConversion.business_id == business_id,
                OfflineConversion.created_at >= start_date
            )
        ).all()

        total_visits = len(all_conversions)
        linked_conversations = len([c for c in all_conversions if c.conversation_id])
        purchased = len([c for c in all_conversions if c.purchased])

        total_revenue = sum(c.purchase_amount or 0 for c in all_conversions if c.purchased)

        return {
            "period_days": days,
            "total_visits": total_visits,
            "visits_linked_to_online": linked_conversations,
            "visits_converted_to_purchase": purchased,
            "conversion_rate": purchased / total_visits if total_visits else 0,
            "total_revenue": float(total_revenue),
            "avg_transaction_value": float(total_revenue / purchased) if purchased else 0,
        }

    @staticmethod
    def get_proximity_trigger_effectiveness(
        business_id: UUID,
        trigger_name: str,
        days: int = 30,
        db: Optional[Session] = None
    ) -> dict:
        """Measure effectiveness of proximity trigger (how many lead to actual visit)."""
        if not db:
            raise ValueError("Database session required")

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Proximity events triggered
        events = db.query(GeoProximityEvent).filter(
            and_(
                GeoProximityEvent.business_id == business_id,
                GeoProximityEvent.trigger_name == trigger_name,
                GeoProximityEvent.created_at >= start_date
            )
        ).all()

        total_triggered = len(events)
        executed = len([e for e in events if e.automation_triggered])

        # How many of these led to actual visits
        email_matches = len([e for e in events if e.visitor_email])
        phone_matches = len([e for e in events if e.visitor_phone])
        visits_from_events = len([e for e in events if e.conversation_id and e.automation_triggered])

        return {
            "trigger_name": trigger_name,
            "period_days": days,
            "total_proximity_events": total_triggered,
            "automations_executed": executed,
            "execution_rate": executed / total_triggered if total_triggered else 0,
            "visitor_contacts_captured": email_matches + phone_matches,
            "visits_from_trigger": visits_from_events,
            "trigger_to_visit_rate": visits_from_events / executed if executed else 0,
        }
