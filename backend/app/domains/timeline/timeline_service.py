"""Customer timeline service."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.domains.timeline.timeline_models import (
    CustomerEvent, EventTimeline, TimelineMetadata, EventFilter, TimelineMetrics,
    EventType, EventChannel, EventOutcome
)

logger = logging.getLogger(__name__)


class TimelineService:
    """Manage customer timeline & activity feed."""

    @staticmethod
    def log_event(
        business_id: UUID,
        customer_id: UUID,
        event_type: str,
        channel: str,
        title: str,
        event_data: dict,
        description: Optional[str] = None,
        outcome: str = EventOutcome.SUCCESS.value,
        revenue_impact: Optional[str] = None,
        estimated_value: Optional[int] = None,
        created_by: Optional[UUID] = None,
        db: Session = None
    ) -> dict:
        """Log customer event."""
        if not db:
            raise ValueError("Database session required")

        event = CustomerEvent(
            business_id=business_id,
            customer_id=customer_id,
            event_type=event_type,
            channel=channel,
            title=title,
            description=description,
            event_data=event_data,
            outcome=outcome,
            revenue_impact=revenue_impact,
            estimated_value=estimated_value,
            created_by=created_by,
            engagement_score=TimelineService._calculate_engagement_score(event_type, outcome)
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        # Update timeline summary
        TimelineService._update_timeline_summary(business_id, customer_id, db)

        logger.info(f"Event logged: {event_type} for customer {customer_id}")

        return {
            "event_id": str(event.id),
            "event_type": event_type,
            "channel": channel,
            "timestamp": event.created_at.isoformat()
        }

    @staticmethod
    def get_customer_timeline(
        customer_id: UUID,
        business_id: UUID,
        limit: int = 50,
        offset: int = 0,
        event_types: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        db: Session = None
    ) -> List[dict]:
        """Get customer timeline."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(CustomerEvent).filter(
            CustomerEvent.customer_id == customer_id,
            CustomerEvent.business_id == business_id
        )

        if event_types:
            query = query.filter(CustomerEvent.event_type.in_(event_types))
        if channels:
            query = query.filter(CustomerEvent.channel.in_(channels))

        events = query.order_by(desc(CustomerEvent.created_at)).offset(offset).limit(limit).all()

        return [
            {
                "event_id": str(e.id),
                "event_type": e.event_type,
                "channel": e.channel,
                "title": e.title,
                "description": e.description,
                "outcome": e.outcome,
                "engagement_score": e.engagement_score,
                "revenue_impact": e.revenue_impact,
                "estimated_value": e.estimated_value,
                "is_important": e.is_important,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]

    @staticmethod
    def get_timeline_summary(
        customer_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Get timeline summary."""
        if not db:
            raise ValueError("Database session required")

        timeline = db.query(EventTimeline).filter(
            EventTimeline.customer_id == customer_id,
            EventTimeline.business_id == business_id
        ).first()

        if not timeline:
            return {"message": "No timeline found"}

        return {
            "total_events": timeline.total_events,
            "last_event": timeline.last_event_at.isoformat() if timeline.last_event_at else None,
            "first_event": timeline.first_event_at.isoformat() if timeline.first_event_at else None,
            "email_count": timeline.email_count,
            "sms_count": timeline.sms_count,
            "whatsapp_count": timeline.whatsapp_count,
            "call_count": timeline.call_count,
            "meeting_count": timeline.meeting_count,
            "order_count": timeline.order_count,
            "deal_count": timeline.deal_count,
            "avg_engagement_score": timeline.avg_engagement_score,
            "important_events_count": timeline.important_events_count,
            "total_revenue_impact": timeline.total_revenue_impact,
            "channel_breakdown": timeline.channel_breakdown,
        }

    @staticmethod
    def get_event_stream(
        business_id: UUID,
        limit: int = 50,
        db: Session = None
    ) -> List[dict]:
        """Get live event stream across all customers."""
        if not db:
            raise ValueError("Database session required")

        events = db.query(CustomerEvent).filter(
            CustomerEvent.business_id == business_id
        ).order_by(desc(CustomerEvent.created_at)).limit(limit).all()

        return [
            {
                "event_id": str(e.id),
                "customer_id": str(e.customer_id),
                "event_type": e.event_type,
                "channel": e.channel,
                "title": e.title,
                "outcome": e.outcome,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]

    @staticmethod
    def search_events(
        business_id: UUID,
        query_text: str,
        limit: int = 50,
        db: Session = None
    ) -> List[dict]:
        """Search events by title/description."""
        if not db:
            raise ValueError("Database session required")

        events = db.query(CustomerEvent).filter(
            CustomerEvent.business_id == business_id,
            (CustomerEvent.title.ilike(f"%{query_text}%")) |
            (CustomerEvent.description.ilike(f"%{query_text}%"))
        ).order_by(desc(CustomerEvent.created_at)).limit(limit).all()

        return [
            {
                "event_id": str(e.id),
                "customer_id": str(e.customer_id),
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]

    @staticmethod
    def mark_event_important(
        event_id: UUID,
        is_important: bool,
        db: Session = None
    ) -> dict:
        """Mark event as important/star."""
        if not db:
            raise ValueError("Database session required")

        event = db.query(CustomerEvent).filter(CustomerEvent.id == event_id).first()
        if not event:
            raise ValueError("Event not found")

        event.is_important = is_important
        db.commit()

        return {"event_id": str(event_id), "marked_important": is_important}

    @staticmethod
    def save_event_filter(
        business_id: UUID,
        user_id: UUID,
        name: str,
        event_types: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        outcomes: Optional[List[str]] = None,
        db: Session = None
    ) -> dict:
        """Save timeline filter."""
        if not db:
            raise ValueError("Database session required")

        filter_obj = EventFilter(
            business_id=business_id,
            user_id=user_id,
            name=name,
            event_types=event_types or [],
            channels=channels or [],
            outcomes=outcomes or []
        )

        db.add(filter_obj)
        db.commit()
        db.refresh(filter_obj)

        return {"filter_id": str(filter_obj.id), "name": name}

    @staticmethod
    def get_event_filters(
        business_id: UUID,
        user_id: UUID,
        db: Session = None
    ) -> List[dict]:
        """Get saved filters."""
        if not db:
            raise ValueError("Database session required")

        filters = db.query(EventFilter).filter(
            EventFilter.business_id == business_id,
            EventFilter.user_id == user_id
        ).order_by(desc(EventFilter.is_favorite)).all()

        return [
            {
                "filter_id": str(f.id),
                "name": f.name,
                "event_types": f.event_types,
                "channels": f.channels,
                "is_favorite": f.is_favorite,
            }
            for f in filters
        ]

    @staticmethod
    def get_timeline_metrics(
        business_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get timeline metrics."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        total_events = db.query(func.count(CustomerEvent.id)).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).scalar() or 0

        active_customers = db.query(func.count(func.distinct(CustomerEvent.customer_id))).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).scalar() or 0

        # Event type breakdown
        event_type_counts = db.query(
            CustomerEvent.event_type,
            func.count(CustomerEvent.id)
        ).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).group_by(CustomerEvent.event_type).all()

        # Channel breakdown
        channel_counts = db.query(
            CustomerEvent.channel,
            func.count(CustomerEvent.id)
        ).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).group_by(CustomerEvent.channel).all()

        avg_engagement = db.query(func.avg(CustomerEvent.engagement_score)).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).scalar() or 0

        total_revenue = db.query(func.sum(CustomerEvent.estimated_value)).filter(
            CustomerEvent.business_id == business_id,
            CustomerEvent.created_at >= cutoff
        ).scalar() or 0

        return {
            "total_events": total_events,
            "active_customers": active_customers,
            "avg_events_per_customer": round(total_events / max(active_customers, 1), 2),
            "avg_engagement_score": round(float(avg_engagement), 2),
            "total_revenue_impact": total_revenue,
            "event_types": {et: count for et, count in event_type_counts},
            "channels": {ch: count for ch, count in channel_counts},
            "days": days
        }

    @staticmethod
    def _calculate_engagement_score(event_type: str, outcome: str) -> int:
        """Calculate engagement score for event."""
        base_scores = {
            EventType.EMAIL_CLICKED.value: 90,
            EventType.EMAIL_OPENED.value: 60,
            EventType.WHATSAPP_READ.value: 80,
            EventType.CALL_INCOMING.value: 100,
            EventType.MEETING_COMPLETED.value: 100,
            EventType.ORDER_PAID.value: 100,
            EventType.DEAL_WON.value: 100,
            EventType.SMS_DELIVERED.value: 40,
        }

        score = base_scores.get(event_type, 50)

        if outcome == EventOutcome.FAILED.value:
            score = max(0, score - 30)
        elif outcome == EventOutcome.NO_SHOW.value:
            score = max(0, score - 40)

        return score

    @staticmethod
    def _update_timeline_summary(
        business_id: UUID,
        customer_id: UUID,
        db: Session = None
    ) -> None:
        """Update timeline summary."""
        if not db:
            return

        timeline = db.query(EventTimeline).filter(
            EventTimeline.customer_id == customer_id,
            EventTimeline.business_id == business_id
        ).first()

        if not timeline:
            timeline = EventTimeline(
                business_id=business_id,
                customer_id=customer_id
            )
            db.add(timeline)

        # Recalculate stats
        events = db.query(CustomerEvent).filter(
            CustomerEvent.customer_id == customer_id,
            CustomerEvent.business_id == business_id
        ).all()

        timeline.total_events = len(events)
        if events:
            timeline.last_event_at = max(e.created_at for e in events)
            timeline.first_event_at = min(e.created_at for e in events)

        # Count by event type
        for event in events:
            if event.event_type.startswith("email_"):
                timeline.email_count += 1
            elif event.event_type.startswith("sms_"):
                timeline.sms_count += 1
            elif event.event_type.startswith("whatsapp_"):
                timeline.whatsapp_count += 1
            elif event.event_type.startswith("call_"):
                timeline.call_count += 1
            elif event.event_type.startswith("meeting_"):
                timeline.meeting_count += 1
            elif event.event_type.startswith("order_"):
                timeline.order_count += 1
            elif event.event_type.startswith("deal_"):
                timeline.deal_count += 1

        timeline.avg_engagement_score = round(sum(e.engagement_score for e in events) / max(len(events), 1))
        timeline.important_events_count = sum(1 for e in events if e.is_important)
        timeline.total_revenue_impact = sum(e.estimated_value or 0 for e in events)

        db.commit()
