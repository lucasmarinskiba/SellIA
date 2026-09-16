"""Closed-loop FOMO feedback system."""

from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.fomo_models import ConversionEvent, FOMABTest
from app.domains.seo_config.analytics_models import PublicationLinkMetrics

logger = get_logger(__name__)


class FOMAFeedbackLoop:
    """Closed-loop learning: conversions → refine predictions → better FOMO."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_conversion_feedback(
        self,
        business_id: UUID,
        fomo_id: UUID,
        link_id: UUID,
        converted: bool,
    ) -> dict:
        """Record conversion feedback for a FOMO copy.

        Used to refine predictive models over time.
        """
        feedback = {
            "business_id": str(business_id),
            "fomo_id": str(fomo_id),
            "link_id": str(link_id),
            "converted": converted,
            "recorded_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Conversion feedback: FOMO {fomo_id} -> {converted}")
        return feedback

    async def get_prediction_accuracy(
        self,
        business_id: UUID,
        days: int = 30,
    ) -> dict:
        """Calculate how accurate predictions have been.

        Compares predicted conversion probability vs actual conversions.
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # Get all conversions in period
        result = await self.db.execute(
            select(
                ConversionEvent.fomo_variant_id,
                func.count(ConversionEvent.id).label("conversion_count"),
            )
            .where(
                ConversionEvent.business_id == business_id,
                ConversionEvent.created_at >= start_date,
            )
            .group_by(ConversionEvent.fomo_variant_id)
        )

        actual_conversions = {row[0]: row[1] for row in result.all()}
        total_conversions = sum(actual_conversions.values())

        # Get all FOMO copies with their scores
        result = await self.db.execute(
            select(PublicationLinkFOMO).where(
                PublicationLinkFOMO.business_id == business_id,
                PublicationLinkFOMO.created_at >= start_date,
            )
        )
        fomo_copies = result.scalars().all()

        # Calculate accuracy (higher FOMO score = more conversions?)
        scored_copies = []
        for fomo in fomo_copies:
            conversions = actual_conversions.get(fomo.id, 0)
            scored_copies.append({
                "fomo_id": str(fomo.id),
                "fomo_score": float(fomo.fomo_score),
                "actual_conversions": conversions,
            })

        # Sort by FOMO score and check if order matches conversions
        by_score = sorted(scored_copies, key=lambda x: x["fomo_score"], reverse=True)
        by_conversions = sorted(scored_copies, key=lambda x: x["actual_conversions"], reverse=True)

        # Spearman rank correlation proxy (simplified)
        accuracy = 0.0
        if len(by_score) > 1:
            matches = sum(
                1 for i, item in enumerate(by_score)
                if item in by_conversions[: i + 2]
            )
            accuracy = (matches / len(by_score)) * 100 if by_score else 0.0

        return {
            "period_days": days,
            "total_conversions": total_conversions,
            "fomo_copies_tested": len(fomo_copies),
            "prediction_accuracy": float(min(100.0, accuracy)),
            "status": "improving" if accuracy > 60 else "calibrating",
            "recommendation": "Keep current model" if accuracy > 70 else "Retrain model with new data",
        }

    async def get_learning_velocity(
        self,
        business_id: UUID,
    ) -> dict:
        """Get how fast the system is improving (learning velocity).

        Compares prediction accuracy over time windows.
        """
        week_ago = (datetime.utcnow() - timedelta(days=7)).date()
        month_ago = (datetime.utcnow() - timedelta(days=30)).date()

        week_accuracy = await self.get_prediction_accuracy(business_id, days=7)
        month_accuracy = await self.get_prediction_accuracy(business_id, days=30)

        velocity = week_accuracy["prediction_accuracy"] - month_accuracy["prediction_accuracy"]

        return {
            "week_accuracy": week_accuracy["prediction_accuracy"],
            "month_accuracy": month_accuracy["prediction_accuracy"],
            "learning_velocity": float(velocity),
            "trend": "positive" if velocity > 2 else "stable" if velocity > -2 else "declining",
            "conversions_this_week": week_accuracy["total_conversions"],
            "conversions_this_month": month_accuracy["total_conversions"],
        }

    async def get_fomo_effectiveness_trend(
        self,
        link_id: UUID,
        days: int = 30,
    ) -> dict:
        """Track FOMO effectiveness over time for a specific link."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        result = await self.db.execute(
            select(
                PublicationLinkMetrics.metric_date,
                func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"),
                func.sum(PublicationLinkMetrics.conversions).label("total_conversions"),
            )
            .where(
                PublicationLinkMetrics.link_id == link_id,
                PublicationLinkMetrics.metric_date >= start_date,
            )
            .group_by(PublicationLinkMetrics.metric_date)
            .order_by(PublicationLinkMetrics.metric_date)
        )

        daily_data = []
        for row in result.all():
            daily_data.append({
                "date": row[0].isoformat(),
                "avg_ctr": float(row[1]) if row[1] else 0.0,
                "conversions": int(row[2]) if row[2] else 0,
            })

        # Calculate trend
        if len(daily_data) >= 2:
            first_week_ctr = sum(d["avg_ctr"] for d in daily_data[:7]) / min(7, len(daily_data))
            last_week_ctr = sum(d["avg_ctr"] for d in daily_data[-7:]) / min(7, len(daily_data))
            trend_pct = ((last_week_ctr - first_week_ctr) / first_week_ctr * 100) if first_week_ctr > 0 else 0.0
        else:
            trend_pct = 0.0

        return {
            "link_id": str(link_id),
            "period_days": days,
            "daily_data": daily_data,
            "trend_percentage": float(trend_pct),
            "trend": "improving" if trend_pct > 5 else "stable" if trend_pct > -5 else "declining",
            "recommendation": "Keep current FOMO copy" if trend_pct > 0 else "Consider regenerating",
        }
