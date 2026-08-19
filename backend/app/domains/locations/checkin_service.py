"""Location check-in service — handle visitor/staff check-ins."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.domains.locations.checkin_models import LocationCheckin, StaffCheckin, LocationFeedback, CheckinType, CheckinStatus

logger = logging.getLogger(__name__)


class LocationCheckinService:
    """Service for managing location check-ins."""

    @staticmethod
    def checkin_visitor(
        location_id: UUID,
        business_id: UUID,
        checkin_type: CheckinType,
        visitor_phone: Optional[str] = None,
        visitor_email: Optional[str] = None,
        visitor_name: Optional[str] = None,
        user_id: Optional[UUID] = None,
        qr_code: Optional[str] = None,
        db: Optional[Session] = None
    ) -> LocationCheckin:
        """Log visitor check-in (walk-in, QR, appointment, etc)."""
        if not db:
            raise ValueError("Database session required")

        checkin = LocationCheckin(
            location_id=location_id,
            business_id=business_id,
            checkin_type=checkin_type,
            user_id=user_id,
            visitor_phone=visitor_phone,
            visitor_email=visitor_email,
            visitor_name=visitor_name,
            qr_code=qr_code,
            status=CheckinStatus.CHECKED_IN,
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        logger.info(f"Visitor checked in at {location_id}: {checkin_type}")

        return checkin

    @staticmethod
    def checkout_visitor(
        checkin_id: UUID,
        visited_sections: list[str] = None,
        db: Optional[Session] = None
    ) -> LocationCheckin:
        """Log visitor check-out, calculate dwell time."""
        if not db:
            raise ValueError("Database session required")

        checkin = db.query(LocationCheckin).filter(LocationCheckin.id == checkin_id).first()

        if not checkin:
            raise ValueError(f"Check-in {checkin_id} not found")

        checkin.checkout_time = datetime.now(timezone.utc)
        checkin.status = CheckinStatus.CHECKED_OUT

        # Calculate dwell time
        if checkin.checkin_time:
            dwell = checkin.checkout_time - checkin.checkin_time
            checkin.dwell_seconds = int(dwell.total_seconds())

        # Record sections visited
        if visited_sections:
            checkin.visited_sections = visited_sections

        db.commit()
        db.refresh(checkin)

        logger.info(f"Visitor checked out: {checkin.dwell_seconds}s dwell")

        return checkin

    @staticmethod
    def staff_checkin(
        location_id: UUID,
        business_id: UUID,
        staff_id: UUID,
        staff_name: str,
        staff_role: str,
        db: Optional[Session] = None
    ) -> StaffCheckin:
        """Log staff shift start."""
        if not db:
            raise ValueError("Database session required")

        checkin = StaffCheckin(
            location_id=location_id,
            business_id=business_id,
            staff_id=staff_id,
            staff_name=staff_name,
            staff_role=staff_role,
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        logger.info(f"Staff {staff_name} checked in to {location_id}")

        return checkin

    @staticmethod
    def staff_checkout(
        staff_checkin_id: UUID,
        visitors_engaged: int = 0,
        demos_conducted: int = 0,
        sales_assisted: int = 0,
        db: Optional[Session] = None
    ) -> StaffCheckin:
        """Log staff shift end, record performance."""
        if not db:
            raise ValueError("Database session required")

        checkin = db.query(StaffCheckin).filter(StaffCheckin.id == staff_checkin_id).first()

        if not checkin:
            raise ValueError(f"Staff check-in {staff_checkin_id} not found")

        checkin.checkout_time = datetime.now(timezone.utc)
        checkin.visitors_engaged = visitors_engaged
        checkin.demos_conducted = demos_conducted
        checkin.sales_assisted = sales_assisted

        db.commit()
        db.refresh(checkin)

        logger.info(f"Staff {checkin.staff_name} checked out: {visitors_engaged} visitors, {sales_assisted} sales")

        return checkin

    @staticmethod
    def submit_feedback(
        location_id: UUID,
        business_id: UUID,
        nps_score: Optional[int] = None,
        comment: Optional[str] = None,
        topics: list[str] = None,
        checkin_id: Optional[UUID] = None,
        staff_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> LocationFeedback:
        """Collect visitor feedback via QR/app."""
        if not db:
            raise ValueError("Database session required")

        # Determine sentiment from NPS
        sentiment = None
        if nps_score is not None:
            if nps_score >= 8:
                sentiment = "positive"
            elif nps_score <= 6:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        feedback = LocationFeedback(
            location_id=location_id,
            business_id=business_id,
            checkin_id=checkin_id,
            staff_id=staff_id,
            nps_score=nps_score,
            sentiment=sentiment,
            comment=comment,
            topics=topics or [],
            requires_followup=sentiment == "negative" if sentiment else False,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"Feedback submitted at {location_id}: NPS {nps_score}")

        return feedback

    @staticmethod
    def get_location_checkin_summary(
        location_id: UUID,
        hours: int = 24,
        db: Optional[Session] = None
    ) -> dict:
        """Get real-time checkin summary for location."""
        if not db:
            raise ValueError("Database session required")

        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Active visitors (checked in, not out)
        active = db.query(LocationCheckin).filter(
            LocationCheckin.location_id == location_id,
            LocationCheckin.checkin_time >= cutoff,
            LocationCheckin.status == CheckinStatus.CHECKED_IN
        ).count()

        # Total visitors
        total = db.query(LocationCheckin).filter(
            LocationCheckin.location_id == location_id,
            LocationCheckin.checkin_time >= cutoff
        ).count()

        # Staff on shift
        staff_on_shift = db.query(StaffCheckin).filter(
            StaffCheckin.location_id == location_id,
            StaffCheckin.checkin_time >= cutoff,
            StaffCheckin.checkout_time.is_(None)
        ).count()

        return {
            "location_id": str(location_id),
            "active_visitors": active,
            "total_visitors_today": total,
            "staff_on_shift": staff_on_shift,
            "period_hours": hours,
        }

    @staticmethod
    def get_staff_performance(
        location_id: UUID,
        staff_id: UUID,
        days: int = 30,
        db: Optional[Session] = None
    ) -> dict:
        """Get staff member's location performance."""
        if not db:
            raise ValueError("Database session required")

        from datetime import timedelta
        from sqlalchemy import func

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        shifts = db.query(StaffCheckin).filter(
            StaffCheckin.location_id == location_id,
            StaffCheckin.staff_id == staff_id,
            StaffCheckin.checkin_time >= cutoff
        ).all()

        total_shifts = len(shifts)
        total_visitors = sum(s.visitors_engaged for s in shifts)
        total_demos = sum(s.demos_conducted for s in shifts)
        total_sales = sum(s.sales_assisted for s in shifts)

        return {
            "staff_id": str(staff_id),
            "period_days": days,
            "total_shifts": total_shifts,
            "total_visitors_engaged": total_visitors,
            "total_demos": total_demos,
            "total_sales_assisted": total_sales,
            "avg_visitors_per_shift": total_visitors / total_shifts if total_shifts else 0,
            "avg_sales_per_shift": total_sales / total_shifts if total_shifts else 0,
        }
