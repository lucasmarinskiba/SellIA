"""Phase 5D: Offline Analytics Service."""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select
from app.domains.offline_analytics.models import (
    OfflineToOnlineAttribution,
    OfflineAnalyticsMetrics,
    LocationFootTrafficHourly,
    PostVisitSequence,
    PostVisitSequenceExecution,
)
from app.domains.locations.models import LocationVisit, OfflineConversion


class OfflineAnalyticsService:
    @staticmethod
    async def create_attribution(
        db: AsyncSession,
        business_id: UUID,
        user_id: UUID,
        first_online_channel: Optional[str] = None,
        first_online_date: Optional[datetime] = None,
        location_visited_id: Optional[UUID] = None,
        location_visit_date: Optional[datetime] = None,
        post_visit_order_date: Optional[datetime] = None,
        post_visit_order_value: float = 0,
        conversion_type: str = "online_to_offline",
    ) -> OfflineToOnlineAttribution:
        time_to_conversion = 0
        if location_visit_date and post_visit_order_date:
            delta = post_visit_order_date - location_visit_date
            time_to_conversion = delta.days

        attribution = OfflineToOnlineAttribution(
            business_id=business_id,
            user_id=user_id,
            first_online_channel=first_online_channel,
            first_online_date=first_online_date,
            location_visited_id=location_visited_id,
            location_visit_date=location_visit_date,
            post_visit_order_date=post_visit_order_date,
            post_visit_order_value=post_visit_order_value,
            time_to_conversion_days=time_to_conversion,
            conversion_type=conversion_type,
        )
        db.add(attribution)
        await db.commit()
        await db.refresh(attribution)
        return attribution

    @staticmethod
    async def calculate_offline_metrics(db: AsyncSession, business_id: UUID) -> OfflineAnalyticsMetrics:
        # Get all location visits
        result = await db.execute(
            select(LocationVisit).where(LocationVisit.business_id == business_id)
        )
        visits = result.scalars().all()
        total_foot_traffic = len(visits)
        unique_visitors = len(set(v.user_id for v in visits))

        # Offline conversions
        result = await db.execute(
            select(OfflineConversion).where(OfflineConversion.business_id == business_id)
        )
        offline_conversions = result.scalars().all()
        total_conversions = len([oc for oc in offline_conversions if oc.purchase_made])
        conversion_rate = (total_conversions / total_foot_traffic * 100) if total_foot_traffic > 0 else 0

        # Avg dwell time
        avg_dwell = sum(v.dwell_minutes for v in visits) / len(visits) if visits else 0

        # Total revenue
        total_revenue = sum(v.purchase_value for v in visits)

        # Attribution conversions
        attributions = db.query(OfflineToOnlineAttribution).filter(
            OfflineToOnlineAttribution.business_id == business_id
        ).all()
        online_to_offline = len([a for a in attributions if a.conversion_type == "online_to_offline"])
        offline_to_online = len([a for a in attributions if a.conversion_type == "offline_to_online"])
        full_loop = len([a for a in attributions if a.conversion_type == "full_loop"])

        # Peak hour
        peak_hour = 0
        if visits:
            hours = [v.entry_time.hour for v in visits if v.entry_time]
            if hours:
                peak_hour = max(set(hours), key=hours.count)

        # Repeat visitor rate
        visitor_counts = {}
        for v in visits:
            visitor_counts[v.user_id] = visitor_counts.get(v.user_id, 0) + 1
        repeat_visitors = len([uid for uid, count in visitor_counts.items() if count > 1])
        repeat_rate = (repeat_visitors / unique_visitors * 100) if unique_visitors > 0 else 0

        # Get or create metrics
        existing = db.query(OfflineAnalyticsMetrics).filter(
            OfflineAnalyticsMetrics.business_id == business_id
        ).first()

        if existing:
            existing.total_foot_traffic = total_foot_traffic
            existing.unique_visitors = unique_visitors
            existing.total_conversions_offline = total_conversions
            existing.conversion_rate_offline = conversion_rate
            existing.avg_dwell_time_minutes = avg_dwell
            existing.total_revenue_from_visits = total_revenue
            existing.online_to_offline_conversions = online_to_offline
            existing.offline_to_online_conversions = offline_to_online
            existing.full_loop_conversions = full_loop
            existing.peak_traffic_hour = peak_hour
            existing.repeat_visitor_rate = repeat_rate
            db.commit()
            db.refresh(existing)
            return existing

        metrics = OfflineAnalyticsMetrics(
            business_id=business_id,
            total_foot_traffic=total_foot_traffic,
            unique_visitors=unique_visitors,
            total_conversions_offline=total_conversions,
            conversion_rate_offline=conversion_rate,
            avg_dwell_time_minutes=avg_dwell,
            total_revenue_from_visits=total_revenue,
            online_to_offline_conversions=online_to_offline,
            offline_to_online_conversions=offline_to_online,
            full_loop_conversions=full_loop,
            peak_traffic_hour=peak_hour,
            repeat_visitor_rate=repeat_rate,
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        return metrics

    @staticmethod
    async def create_post_visit_sequence(
        db: AsyncSession,
        business_id: UUID,
        sequence_name: str,
        trigger_type: str,
        location_id: Optional[UUID] = None,
    ) -> PostVisitSequence:
        seq = PostVisitSequence(
            business_id=business_id,
            sequence_name=sequence_name,
            trigger_type=trigger_type,
            location_id=location_id,
        )
        db.add(seq)
        await db.commit()
        await db.refresh(seq)
        return seq

    @staticmethod
    def execute_post_visit_sequence(
        db: Session,
        business_id: UUID,
        sequence_id: UUID,
        user_id: UUID,
        offline_conversion_id: Optional[UUID] = None,
    ) -> PostVisitSequenceExecution:
        execution = PostVisitSequenceExecution(
            business_id=business_id,
            sequence_id=sequence_id,
            user_id=user_id,
            offline_conversion_id=offline_conversion_id,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def get_attribution_report(
        db: Session,
        business_id: UUID,
        days: int = 30,
    ) -> dict:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        attributions = db.query(OfflineToOnlineAttribution).filter(
            and_(
                OfflineToOnlineAttribution.business_id == business_id,
                OfflineToOnlineAttribution.created_at >= cutoff_date,
            )
        ).all()

        online_to_offline = [a for a in attributions if a.conversion_type == "online_to_offline"]
        offline_to_online = [a for a in attributions if a.conversion_type == "offline_to_online"]
        full_loop = [a for a in attributions if a.conversion_type == "full_loop"]

        return {
            "period_days": days,
            "online_to_offline_conversions": len(online_to_offline),
            "offline_to_online_conversions": len(offline_to_online),
            "full_loop_conversions": len(full_loop),
            "total_revenue_from_attribution": sum(a.post_visit_order_value for a in attributions),
            "avg_time_to_conversion_days": (
                sum(a.time_to_conversion_days for a in attributions) / len(attributions)
                if attributions else 0
            ),
        }
