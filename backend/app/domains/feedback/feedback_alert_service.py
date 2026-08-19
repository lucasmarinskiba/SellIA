"""Real-time feedback alerting + NPS monitoring service."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.feedback.feedback_alert_models import (
    NPSAlert, NPSTrendMetric, SentimentTrend, FeedbackFollowUp,
    FeedbackSentiment, AlertStatus
)

logger = logging.getLogger(__name__)


class FeedbackAlertService:
    """Monitor NPS + trigger alerts on low scores."""

    @staticmethod
    def evaluate_feedback_and_alert(
        feedback_id: UUID,
        location_id: UUID,
        business_id: UUID,
        nps_score: int,
        sentiment: str,
        comment: str = None,
        topics: list = None,
        visitor_email: str = None,
        visitor_phone: str = None,
        visitor_name: str = None,
        db: Session = None
    ) -> dict:
        """Evaluate feedback score. Create alert if NPS < 6."""
        if not db:
            raise ValueError("Database session required")

        if nps_score >= 6:
            return {"alert_triggered": False, "nps_score": nps_score}

        # Low NPS detected
        alert = NPSAlert(
            location_id=location_id,
            business_id=business_id,
            feedback_id=feedback_id,
            nps_score=nps_score,
            sentiment=FeedbackSentiment[sentiment.upper()] if sentiment else FeedbackSentiment.NEGATIVE,
            comment=comment,
            topics=topics or [],
            visitor_email=visitor_email,
            visitor_phone=visitor_phone,
            visitor_name=visitor_name,
            status=AlertStatus.ACTIVE
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.warning(f"Low NPS alert created: {alert.id} (score={nps_score})")

        return {
            "alert_triggered": True,
            "alert_id": str(alert.id),
            "nps_score": nps_score,
            "requires_immediate_attention": nps_score <= 3
        }

    @staticmethod
    def acknowledge_alert(
        alert_id: UUID,
        manager_id: UUID,
        db: Session
    ) -> dict:
        """Manager acknowledges alert."""
        alert = db.query(NPSAlert).filter(NPSAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = manager_id
        alert.acknowledged_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        logger.info(f"Alert acknowledged: {alert_id}")

        return {
            "alert_id": str(alert.id),
            "status": alert.status.value,
            "acknowledged_at": alert.acknowledged_at.isoformat()
        }

    @staticmethod
    def escalate_alert(
        alert_id: UUID,
        assigned_to_staff_id: UUID,
        resolution_plan: str = None,
        db: Session = None
    ) -> dict:
        """Assign staff member to resolve alert."""
        if not db:
            raise ValueError("Database session required")

        alert = db.query(NPSAlert).filter(NPSAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.ESCALATED
        alert.assigned_to_staff_id = assigned_to_staff_id
        alert.assigned_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        # Create follow-up record
        follow_up = FeedbackFollowUp(
            nps_alert_id=alert.id,
            feedback_id=alert.feedback_id,
            visitor_email=alert.visitor_email,
            visitor_phone=alert.visitor_phone,
            assigned_to_staff_id=assigned_to_staff_id,
            initial_nps=alert.nps_score,
            resurvey_scheduled_for=datetime.now(timezone.utc) + timedelta(days=7)
        )

        db.add(follow_up)
        db.commit()

        logger.info(f"Alert escalated: {alert_id} assigned to staff {assigned_to_staff_id}")

        return {
            "alert_id": str(alert.id),
            "status": alert.status.value,
            "assigned_to": str(assigned_to_staff_id),
            "follow_up_id": str(follow_up.id),
            "resurvey_scheduled": follow_up.resurvey_scheduled_for.isoformat()
        }

    @staticmethod
    def resolve_alert(
        alert_id: UUID,
        resolution_notes: str = None,
        db: Session = None
    ) -> dict:
        """Mark alert as resolved."""
        if not db:
            raise ValueError("Database session required")

        alert = db.query(NPSAlert).filter(NPSAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution_notes = resolution_notes

        # Update follow-up
        follow_up = db.query(FeedbackFollowUp).filter(
            FeedbackFollowUp.nps_alert_id == alert.id
        ).first()

        if follow_up:
            follow_up.resolved = True
            follow_up.resolution_details = resolution_notes

        db.commit()
        db.refresh(alert)

        logger.info(f"Alert resolved: {alert_id}")

        return {
            "alert_id": str(alert.id),
            "status": alert.status.value,
            "resolved_at": alert.resolved_at.isoformat()
        }

    @staticmethod
    def get_location_alerts(
        location_id: UUID,
        status_filter: str = None,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get NPS alerts for location."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(NPSAlert).filter(
            NPSAlert.location_id == location_id,
            NPSAlert.created_at >= cutoff
        )

        if status_filter:
            query = query.filter(NPSAlert.status == AlertStatus[status_filter.upper()])

        alerts = query.order_by(NPSAlert.created_at.desc()).all()

        alert_list = [
            {
                "alert_id": str(a.id),
                "nps_score": a.nps_score,
                "sentiment": a.sentiment.value,
                "comment": a.comment,
                "topics": a.topics,
                "status": a.status.value,
                "visitor_name": a.visitor_name,
                "created_at": a.created_at.isoformat(),
                "assigned_to": str(a.assigned_to_staff_id) if a.assigned_to_staff_id else None,
            }
            for a in alerts
        ]

        # Count by status
        status_counts = {
            "active": len([a for a in alerts if a.status == AlertStatus.ACTIVE]),
            "acknowledged": len([a for a in alerts if a.status == AlertStatus.ACKNOWLEDGED]),
            "escalated": len([a for a in alerts if a.status == AlertStatus.ESCALATED]),
            "resolved": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
        }

        return {
            "location_id": str(location_id),
            "total_alerts": len(alert_list),
            "status_counts": status_counts,
            "alerts": alert_list
        }


class NPSDashboardService:
    """NPS metrics + trending."""

    @staticmethod
    def update_nps_metrics(
        location_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Update hourly NPS snapshot for location."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.locations.checkin_models import LocationFeedback

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        hour = now.hour

        # Get feedback from past hour
        hour_cutoff = now - timedelta(hours=1)

        feedback_list = db.query(LocationFeedback).filter(
            LocationFeedback.location_id == location_id,
            LocationFeedback.created_at >= hour_cutoff,
            LocationFeedback.nps_score.isnot(None)
        ).all()

        if not feedback_list:
            return {"updated": False, "reason": "No feedback this hour"}

        # Calculate metrics
        nps_scores = [f.nps_score for f in feedback_list]
        nps_avg = sum(nps_scores) / len(nps_scores)

        promoters = len([s for s in nps_scores if s >= 9])
        passives = len([s for s in nps_scores if 7 <= s < 9])
        detractors = len([s for s in nps_scores if s < 7])

        sentiments = [f.sentiment for f in feedback_list]
        positive = len([s for s in sentiments if s == "positive"])
        neutral = len([s for s in sentiments if s == "neutral"])
        negative = len([s for s in sentiments if s == "negative"])

        # Find top issues
        all_topics = []
        for f in feedback_list:
            if f.topics:
                all_topics.extend(f.topics)

        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        top_issues = sorted(
            [{"topic": t, "count": c} for t, c in topic_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        # Store metric
        metric = NPSTrendMetric(
            location_id=location_id,
            business_id=business_id,
            date=date_str,
            hour=hour,
            nps_avg=Decimal(str(round(nps_avg, 2))),
            promoters_count=promoters,
            passives_count=passives,
            detractors_count=detractors,
            total_responses=len(feedback_list),
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            top_issues=top_issues
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        logger.info(f"NPS metrics updated for {location_id}: avg={nps_avg}")

        return {
            "updated": True,
            "nps_avg": float(nps_avg),
            "promoters": promoters,
            "detractors": detractors,
            "top_issues": top_issues
        }

    @staticmethod
    def get_nps_dashboard(
        location_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get NPS dashboard data."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get daily metrics
        daily_metrics = db.query(NPSTrendMetric).filter(
            NPSTrendMetric.location_id == location_id,
            NPSTrendMetric.hour.is_(None),  # Daily aggregate
            NPSTrendMetric.created_at >= cutoff
        ).order_by(NPSTrendMetric.date).all()

        if not daily_metrics:
            daily_metrics = []

        # Calculate overall stats
        all_scores = [float(m.nps_avg) for m in daily_metrics]
        current_nps = float(daily_metrics[-1].nps_avg) if daily_metrics else 0
        nps_trend_30d = current_nps - float(daily_metrics[0].nps_avg) if len(daily_metrics) > 1 else 0

        # Sentiment trend
        sentiment_data = db.query(SentimentTrend).filter(
            SentimentTrend.location_id == location_id,
            SentimentTrend.date >= cutoff.strftime("%Y-%m-%d")
        ).order_by(SentimentTrend.date).all()

        return {
            "location_id": str(location_id),
            "period_days": days,
            "current_nps": round(current_nps, 1),
            "avg_nps_period": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            "nps_trend_30d": round(nps_trend_30d, 1),
            "data_points": [
                {
                    "date": m.date,
                    "nps_avg": float(m.nps_avg),
                    "promoters": m.promoters_count,
                    "passives": m.passives_count,
                    "detractors": m.detractors_count,
                    "top_issues": m.top_issues,
                }
                for m in daily_metrics[-30:]  # Last 30 days
            ],
            "sentiment_trend": [
                {
                    "date": s.date,
                    "positive": float(s.positive_pct),
                    "neutral": float(s.neutral_pct),
                    "negative": float(s.negative_pct),
                    "direction": s.direction,
                }
                for s in sentiment_data[-30:]
            ]
        }

    @staticmethod
    def calculate_sentiment_trend(
        location_id: UUID,
        date: str,
        db: Session = None
    ) -> dict:
        """Calculate daily sentiment trend."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.locations.checkin_models import LocationFeedback

        date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        feedback_list = db.query(LocationFeedback).filter(
            LocationFeedback.location_id == location_id,
            LocationFeedback.created_at >= date_start,
            LocationFeedback.created_at < date_end,
            LocationFeedback.sentiment.isnot(None)
        ).all()

        if not feedback_list:
            return {"calculated": False}

        total = len(feedback_list)
        positive = len([f for f in feedback_list if f.sentiment == "positive"])
        neutral = len([f for f in feedback_list if f.sentiment == "neutral"])
        negative = len([f for f in feedback_list if f.sentiment == "negative"])

        # Calculate previous day for comparison
        prev_date_start = date_start - timedelta(days=1)
        prev_date_end = prev_date_start + timedelta(days=1)

        prev_feedback = db.query(LocationFeedback).filter(
            LocationFeedback.location_id == location_id,
            LocationFeedback.created_at >= prev_date_start,
            LocationFeedback.created_at < prev_date_end,
            LocationFeedback.sentiment.isnot(None)
        ).all()

        direction = "stable"
        change = 0
        if prev_feedback:
            prev_negative = len([f for f in prev_feedback if f.sentiment == "negative"])
            change = ((negative - prev_negative) / len(prev_feedback)) * 100
            if change < -5:
                direction = "improving"
            elif change > 5:
                direction = "declining"

        positive_pct = (positive / total * 100) if total else 0
        neutral_pct = (neutral / total * 100) if total else 0
        negative_pct = (negative / total * 100) if total else 0

        trend = SentimentTrend(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            date=date,
            positive_pct=Decimal(str(round(positive_pct, 2))),
            neutral_pct=Decimal(str(round(neutral_pct, 2))),
            negative_pct=Decimal(str(round(negative_pct, 2))),
            direction=direction,
            day_over_day_change=Decimal(str(round(change, 2)))
        )

        db.add(trend)
        db.commit()

        logger.info(f"Sentiment trend calculated: {location_id} on {date}")

        return {
            "calculated": True,
            "date": date,
            "positive_pct": round(positive_pct, 1),
            "neutral_pct": round(neutral_pct, 1),
            "negative_pct": round(negative_pct, 1),
            "direction": direction
        }
