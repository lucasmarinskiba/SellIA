"""BI Services."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.domains.bi.models import FunnelMetrics, CohortMetrics, ChurnPrediction, LtvPrediction, InsightAlert
from app.domains.orders.models import Order
from app.domains.channels.models import Conversation, Message
from app.domains.business_context.models import BusinessContext
from app.domains.analytics.adapters import FunnelAdapter
from app.core.logger import get_logger

logger = get_logger(__name__)


class BiService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_business_context(self, business_id: UUID) -> Optional[BusinessContext]:
        result = await self.db.execute(
            select(BusinessContext).where(BusinessContext.business_id == business_id)
        )
        return result.scalar_one_or_none()

    async def generate_funnel_report(self, business_id: UUID, period: str, period_type: str = "monthly"):
        """Generate funnel metrics for a given period."""
        # Count leads (conversations started)
        leads_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.created_at >= self._period_start(period, period_type),
            )
        )
        leads_count = leads_result.scalar() or 0

        # Count orders
        orders_result = await self.db.execute(
            select(func.count(Order.id), func.sum(Order.total_amount)).where(
                Order.business_id == business_id,
                Order.created_at >= self._period_start(period, period_type),
                Order.status.in_(["paid", "completed"]),
            )
        )
        orders_count, revenue_total = orders_result.one() or (0, Decimal("0"))

        bc = await self._get_business_context(business_id)
        custom_stages = FunnelAdapter.get_stages(bc.business_type if bc else None)

        fm = FunnelMetrics(
            business_id=business_id,
            period=period,
            period_type=period_type,
            leads_count=leads_count,
            orders_count=orders_count or 0,
            revenue_total=revenue_total or Decimal("0"),
            avg_order_value=(revenue_total / orders_count) if orders_count else Decimal("0"),
        )
        fm._custom_stages = custom_stages  # type: ignore
        self.db.add(fm)
        await self.db.commit()
        return fm

    def _period_start(self, period: str, period_type: str) -> datetime:
        now = datetime.now(timezone.utc)
        if period_type == "daily":
            return now - timedelta(days=1)
        if period_type == "weekly":
            return now - timedelta(weeks=1)
        return now - timedelta(days=30)

    async def get_latest_funnel(self, business_id: UUID):
        result = await self.db.execute(
            select(FunnelMetrics)
            .where(FunnelMetrics.business_id == business_id)
            .order_by(FunnelMetrics.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_insight_alerts(self, business_id: UUID, insight_type: str | None = None):
        q = select(InsightAlert).where(
            InsightAlert.business_id == business_id,
            InsightAlert.is_active == True,
        )
        if insight_type:
            q = q.where(InsightAlert.insight_type == insight_type)
        q = q.order_by(InsightAlert.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all()
