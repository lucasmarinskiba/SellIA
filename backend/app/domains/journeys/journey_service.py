"""Customer journey tracking service."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.journeys.journey_models import (
    CustomerJourney, JourneyTouchpoint, JourneyMetrics,
    JourneyChannel, JourneyStage
)

logger = logging.getLogger(__name__)


class CustomerJourneyService:
    """Track and manage customer journeys."""

    @staticmethod
    def start_journey(
        business_id: UUID,
        channel: str,
        customer_email: str = None,
        customer_phone: str = None,
        campaign: str = None,
        source: str = None,
        db: Session = None
    ) -> dict:
        """Start new customer journey."""
        if not db:
            raise ValueError("Database session required")

        journey = CustomerJourney(
            business_id=business_id,
            customer_email=customer_email,
            customer_phone=customer_phone,
            current_stage=JourneyStage.AWARENESS,
            initial_channel=JourneyChannel[channel.upper()],
            initial_campaign=campaign,
            initial_source=source,
            awareness_date=datetime.now(timezone.utc)
        )

        db.add(journey)
        db.commit()
        db.refresh(journey)

        # Log touchpoint
        touchpoint = JourneyTouchpoint(
            journey_id=journey.id,
            business_id=business_id,
            touchpoint_type="initial_contact",
            channel=JourneyChannel[channel.upper()],
            campaign=campaign
        )
        db.add(touchpoint)
        db.commit()

        logger.info(f"Journey started: {journey.id} via {channel}")

        return {
            "journey_id": str(journey.id),
            "stage": journey.current_stage.value,
            "channel": journey.initial_channel.value,
            "started_at": journey.awareness_date.isoformat()
        }

    @staticmethod
    def record_touchpoint(
        journey_id: UUID,
        business_id: UUID,
        touchpoint_type: str,
        channel: str,
        campaign: str = None,
        location_id: UUID = None,
        order_id: str = None,
        db: Session = None
    ) -> dict:
        """Record touchpoint in journey."""
        if not db:
            raise ValueError("Database session required")

        journey = db.query(CustomerJourney).filter(CustomerJourney.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        touchpoint = JourneyTouchpoint(
            journey_id=journey_id,
            business_id=business_id,
            touchpoint_type=touchpoint_type,
            channel=JourneyChannel[channel.upper()],
            campaign=campaign,
            location_id=location_id,
            order_id=order_id
        )

        db.add(touchpoint)

        # Update journey stage based on touchpoint
        if touchpoint_type == "email_opened":
            if journey.current_stage == JourneyStage.AWARENESS:
                journey.current_stage = JourneyStage.CONSIDERATION
                journey.consideration_date = datetime.now(timezone.utc)
            journey.email_opens += 1

        elif touchpoint_type == "proximity_invite_opened":
            if journey.current_stage in [JourneyStage.AWARENESS, JourneyStage.CONSIDERATION]:
                journey.current_stage = JourneyStage.INTENT
                journey.intent_date = datetime.now(timezone.utc)

        elif touchpoint_type == "location_visit":
            if journey.current_stage != JourneyStage.VISIT:
                journey.current_stage = JourneyStage.VISIT
                journey.visit_date = datetime.now(timezone.utc)
            journey.location_visited_id = location_id
            journey.location_visits += 1

        elif touchpoint_type == "order_placed":
            if journey.visit_date and not journey.purchase_date:
                journey.current_stage = JourneyStage.PURCHASE
                journey.purchase_date = datetime.now(timezone.utc)
                journey.is_converted = True
                journey.first_order_id = order_id

        db.commit()
        db.refresh(journey)

        logger.info(f"Touchpoint recorded: {journey_id} - {touchpoint_type}")

        return {
            "journey_id": str(journey_id),
            "touchpoint_type": touchpoint_type,
            "current_stage": journey.current_stage.value,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def get_journey_details(
        journey_id: UUID,
        db: Session = None
    ) -> dict:
        """Get complete journey details."""
        if not db:
            raise ValueError("Database session required")

        journey = db.query(CustomerJourney).filter(CustomerJourney.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        touchpoints = db.query(JourneyTouchpoint).filter(
            JourneyTouchpoint.journey_id == journey_id
        ).order_by(JourneyTouchpoint.created_at).all()

        # Calculate time between stages
        time_awareness_to_visit = None
        if journey.awareness_date and journey.visit_date:
            time_awareness_to_visit = (journey.visit_date - journey.awareness_date).days

        time_visit_to_purchase = None
        if journey.visit_date and journey.purchase_date:
            time_visit_to_purchase = (journey.purchase_date - journey.visit_date).days

        return {
            "journey_id": str(journey.id),
            "customer": {
                "email": journey.customer_email,
                "phone": journey.customer_phone
            },
            "stage": journey.current_stage.value,
            "channel": journey.initial_channel.value,
            "campaign": journey.initial_campaign,
            "converted": journey.is_converted,
            "repeat_customer": journey.is_repeat_customer,
            "metrics": {
                "email_opens": journey.email_opens,
                "web_sessions": journey.web_sessions,
                "location_visits": journey.location_visits,
                "nps_score": journey.nps_score
            },
            "value": {
                "first_order_value": float(journey.first_order_value) if journey.first_order_value else None,
                "lifetime_value": float(journey.total_lifetime_value),
                "repeat_purchases": journey.repeat_purchase_count
            },
            "timeline": {
                "awareness_date": journey.awareness_date.isoformat() if journey.awareness_date else None,
                "visit_date": journey.visit_date.isoformat() if journey.visit_date else None,
                "purchase_date": journey.purchase_date.isoformat() if journey.purchase_date else None,
                "days_awareness_to_visit": time_awareness_to_visit,
                "days_visit_to_purchase": time_visit_to_purchase
            },
            "touchpoints": len(touchpoints)
        }

    @staticmethod
    def calculate_journey_metrics(
        business_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Calculate aggregate journey metrics."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        journeys = db.query(CustomerJourney).filter(
            CustomerJourney.business_id == business_id,
            CustomerJourney.awareness_date >= cutoff
        ).all()

        if not journeys:
            return {"metrics_calculated": False}

        # Stage counts
        awareness = len(journeys)
        consideration = len([j for j in journeys if j.consideration_date])
        intent = len([j for j in journeys if j.intent_date])
        visit = len([j for j in journeys if j.visit_date])
        purchase = len([j for j in journeys if j.purchase_date])
        retention = len([j for j in journeys if j.repeat_purchase_count > 0])

        # Conversion rates
        awareness_to_visit = (visit / max(awareness, 1)) * 100
        visit_to_purchase = (purchase / max(visit, 1)) * 100
        overall_conversion = (purchase / max(awareness, 1)) * 100

        # Channel breakdown
        channels = {}
        for j in journeys:
            channel = j.initial_channel.value
            channels[channel] = channels.get(channel, 0) + 1

        top_channel = max(channels.items(), key=lambda x: x[1]) if channels else (None, 0)

        # LTV
        ltv_values = [float(j.total_lifetime_value) for j in journeys if j.total_lifetime_value > 0]
        avg_ltv = sum(ltv_values) / len(ltv_values) if ltv_values else 0

        # Time metrics
        times_awareness_to_visit = []
        for j in journeys:
            if j.awareness_date and j.visit_date:
                days_diff = (j.visit_date - j.awareness_date).days
                times_awareness_to_visit.append(days_diff)

        avg_time_to_visit = sum(times_awareness_to_visit) / len(times_awareness_to_visit) if times_awareness_to_visit else None

        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metrics = JourneyMetrics(
            business_id=business_id,
            date=date,
            awareness_count=awareness,
            consideration_count=consideration,
            intent_count=intent,
            visit_count=visit,
            purchase_count=purchase,
            retention_count=retention,
            awareness_to_visit=Decimal(str(round(awareness_to_visit, 2))),
            visit_to_purchase=Decimal(str(round(visit_to_purchase, 2))),
            overall_conversion=Decimal(str(round(overall_conversion, 2))),
            top_channel_visits=top_channel[0] if top_channel else None,
            top_channel_count=top_channel[1] if top_channel else 0,
            avg_ltv=Decimal(str(round(avg_ltv, 2))),
            avg_time_to_visit_days=int(avg_time_to_visit) if avg_time_to_visit else None
        )

        db.add(metrics)
        db.commit()

        logger.info(f"Journey metrics calculated: {business_id}")

        return {
            "metrics_calculated": True,
            "period_days": days,
            "funnel": {
                "awareness": awareness,
                "consideration": consideration,
                "visit": visit,
                "purchase": purchase
            },
            "conversion_rates": {
                "awareness_to_visit_pct": round(awareness_to_visit, 2),
                "visit_to_purchase_pct": round(visit_to_purchase, 2),
                "overall_pct": round(overall_conversion, 2)
            },
            "top_channel": top_channel[0] if top_channel else None,
            "avg_ltv": round(avg_ltv, 2),
            "avg_days_to_visit": avg_time_to_visit
        }
