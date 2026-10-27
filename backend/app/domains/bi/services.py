"""BI services: the business funnel, computed on demand from the business's own records.

Nothing is persisted here. A funnel is a read of the current data for a window; storing it would have meant
writing into ``funnel_metrics`` with NOT NULL columns for figures this codebase cannot compute. So:

* ``leads_count``    -- conversations started in the window (a conversation is the lead's first contact);
* ``orders_count``   -- orders in a paid or fulfilled status, and ``revenue_total`` / ``avg_order_value`` from them;
* everything else is ``None``: qualification, deals, repeat customers and the rates that depend on them.
  Orders carry no customer key (the buyer's email and phone are encrypted), so repeat purchases cannot be
  counted reliably, and no qualification or deal field is recorded on conversations.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.models import InsightAlert
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order, OrderStatus

# Statuses that mean money was actually committed: paid, shipped or delivered.
REVENUE_STATUSES = (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED)
WINDOWS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1), "monthly": timedelta(days=30)}


class BiService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def window_start(period_type: str, now: datetime | None = None) -> datetime:
        end = now or datetime.now(timezone.utc)
        return end - WINDOWS.get(period_type, WINDOWS["monthly"])

    async def generate_funnel_report(
        self, business_id: UUID, period: str, period_type: str = "monthly", now: datetime | None = None
    ) -> dict:
        """The funnel for the window ending now. Returns the response fields; persists nothing."""
        if period_type not in WINDOWS:
            raise ValueError(f"period_type inválido: {period_type} (usar daily, weekly o monthly)")
        start = self.window_start(period_type, now)

        leads = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.created_at >= start,
            )
        )
        orders = await self.db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.business_id == business_id,
                Order.created_at >= start,
                Order.status.in_(REVENUE_STATUSES),
            )
        )
        orders_count, revenue = orders.one()
        orders_count = int(orders_count or 0)
        revenue_total = Decimal(str(revenue or 0))

        return {
            "id": uuid4(),  # not stored: the identifier only names this computed response
            "business_id": business_id,
            "period": period,
            "period_type": period_type,
            "leads_count": int(leads.scalar() or 0),
            "qualified_count": None,
            "deals_count": None,
            "orders_count": orders_count,
            "repeat_orders_count": None,
            "conversion_lead_to_qualified": None,
            "conversion_qualified_to_deal": None,
            "conversion_deal_to_order": None,
            "conversion_order_to_repeat": None,
            "revenue_total": revenue_total,
            "avg_order_value": (revenue_total / orders_count).quantize(Decimal("0.01")) if orders_count else None,
            "created_at": now or datetime.now(timezone.utc),
        }

    async def get_latest_funnel(self, business_id: UUID) -> dict:
        """The current monthly funnel (computed now; there is no stored history to read)."""
        return await self.generate_funnel_report(business_id, period=datetime.now(timezone.utc).strftime("%Y-%m"))

    async def list_insight_alerts(self, business_id: UUID, insight_type: str | None = None):
        """Alerts written by the analytics engine (read-only here)."""
        q = select(InsightAlert).where(
            InsightAlert.business_id == business_id,
            InsightAlert.is_active.is_(True),
        )
        if insight_type:
            q = q.where(InsightAlert.insight_type == insight_type)
        q = q.order_by(InsightAlert.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all()
