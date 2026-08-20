"""Attribution service."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.attribution.attribution_models import (
    Touchpoint, CustomerJourney, AttributionCredit, ChannelPerformance, AttributionMetrics
)

logger = logging.getLogger(__name__)


class AttributionService:
    """Multi-touch attribution calculations."""

    @staticmethod
    def log_touchpoint(business_id: UUID, customer_id: UUID, channel: str, source: str, interaction_type: str, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        touchpoint = Touchpoint(
            business_id=business_id,
            customer_id=customer_id,
            channel=channel,
            source=source,
            interaction_type=interaction_type,
            touched_at=datetime.now(timezone.utc)
        )
        db.add(touchpoint)
        db.commit()
        logger.info(f"Touchpoint logged: {touchpoint.id} | {channel}")
        return {"touchpoint_id": str(touchpoint.id), "channel": channel}

    @staticmethod
    def attribute_revenue(order_id: UUID, business_id: UUID, order_value: float, attribution_model: str, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        # Find customer journey touchpoints
        journey = db.query(CustomerJourney).filter(
            CustomerJourney.order_id == order_id,
            CustomerJourney.business_id == business_id
        ).first()
        
        if not journey:
            return {"status": "error", "error": "Journey not found"}
        
        touchpoints = db.query(Touchpoint).filter(
            Touchpoint.customer_id == journey.customer_id,
            Touchpoint.touched_at <= journey.converted_at
        ).order_by(Touchpoint.touched_at).all()
        
        if not touchpoints:
            return {"status": "error", "error": "No touchpoints found"}
        
        # Apply attribution model
        total_touchpoints = len(touchpoints)
        credits = {}
        
        if attribution_model == "first_touch":
            credits[touchpoints[0].id] = 100.0
        elif attribution_model == "last_touch":
            credits[touchpoints[-1].id] = 100.0
        elif attribution_model == "linear":
            credit_per_touch = 100.0 / total_touchpoints
            for tp in touchpoints:
                credits[tp.id] = credit_per_touch
        elif attribution_model == "time_decay":
            total_weight = sum(range(1, total_touchpoints + 1))
            for i, tp in enumerate(touchpoints):
                weight = (i + 1) / total_weight
                credits[tp.id] = weight * 100.0
        
        # Create attribution credits
        for tp_id, percentage in credits.items():
            credit = AttributionCredit(
                business_id=business_id,
                order_id=order_id,
                touchpoint_id=tp_id,
                customer_id=journey.customer_id,
                attribution_model=attribution_model,
                credit_percentage=percentage,
                credited_amount=order_value * (percentage / 100.0),
                channel=next((tp.channel for tp in touchpoints if tp.id == tp_id), "unknown")
            )
            db.add(credit)
        
        db.commit()
        logger.info(f"Revenue attributed for order {order_id}: model={attribution_model}")
        return {"order_id": str(order_id), "credits_created": len(credits), "model": attribution_model}

    @staticmethod
    def get_channel_performance(business_id: UUID, days: int = 30, db: Session = None) -> List[dict]:
        if not db:
            raise ValueError("Database session required")
        
        performance = db.query(ChannelPerformance).filter(
            ChannelPerformance.business_id == business_id
        ).order_by(desc(ChannelPerformance.total_revenue)).all()
        
        return [
            {
                "channel": p.channel,
                "touchpoint_count": p.touchpoint_count,
                "conversion_count": p.conversion_count,
                "total_revenue": p.total_revenue,
                "conversion_rate": p.conversion_rate,
                "roi": p.roi
            }
            for p in performance
        ]

    @staticmethod
    def get_metrics(business_id: UUID, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        metrics = db.query(AttributionMetrics).filter(
            AttributionMetrics.business_id == business_id
        ).first()
        
        if not metrics:
            return {"message": "No metrics found"}
        
        return {
            "total_journeys": metrics.total_journeys,
            "conversion_journeys": metrics.conversion_journeys,
            "avg_journey_length": metrics.avg_journey_length,
            "total_attributed_revenue": metrics.total_attributed_revenue,
            "top_first_touch_channel": metrics.top_first_touch_channel,
            "top_last_touch_channel": metrics.top_last_touch_channel
        }
