"""Business Intelligence & Analytics Services.

Funnel analysis, cohorts, churn prediction, LTV estimation, and insight alerts.
"""

import uuid
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.models import (
    FunnelMetric, CohortMetric, ChurnPrediction, LtvPrediction, InsightAlert,
    FunnelStage, ChurnRiskLevel,
)
from app.domains.channels.models import Conversation, Message
from app.domains.orders.models import Order
from app.domains.crm.models import Deal
from app.domains.business_context.models import BusinessContext
from app.domains.analytics.adapters import (
    FunnelAdapter, ChurnAdapter, LtvAdapter, AlertAdapter,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class BusinessIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_business_context(self, business_id: uuid.UUID) -> Optional[BusinessContext]:
        result = await self.db.execute(
            select(BusinessContext).where(BusinessContext.business_id == business_id)
        )
        return result.scalar_one_or_none()

    # ========== Funnel Analysis ==========

    async def calculate_funnel(self, business_id: uuid.UUID, period: str, period_type: str = "monthly") -> FunnelMetric:
        """Calculate funnel metrics for a period (e.g., '2024-01')."""
        # Parse period
        if period_type == "monthly":
            start = datetime.strptime(period, "%Y-%m").replace(tzinfo=timezone.utc)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1)
        else:
            start = datetime.now(timezone.utc) - timedelta(days=30)
            end = datetime.now(timezone.utc)

        # Leads
        leads_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.created_at >= start,
                Conversation.created_at <= end,
            )
        )
        leads = leads_result.scalar() or 0

        # Qualified (has email or phone)
        qualified_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.created_at >= start,
                Conversation.created_at <= end,
                and_(Conversation.lead_email.isnot(None), Conversation.lead_phone.isnot(None)),
            )
        )
        qualified = qualified_result.scalar() or 0

        # Deals
        deals_result = await self.db.execute(
            select(func.count(Deal.id)).where(
                Deal.business_id == business_id,
                Deal.created_at >= start,
                Deal.created_at <= end,
            )
        )
        deals = deals_result.scalar() or 0

        # Orders
        orders_result = await self.db.execute(
            select(func.count(Order.id), func.sum(Order.total_amount), func.avg(Order.total_amount)).where(
                Order.business_id == business_id,
                Order.created_at >= start,
                Order.created_at <= end,
                Order.is_active == True,
            )
        )
        orders_row = orders_result.first()
        orders = orders_row[0] or 0
        revenue = Decimal(str(orders_row[1] or 0))
        aov = Decimal(str(orders_row[2] or 0))

        # Repeat orders (customers with >1 order in period)
        repeat_result = await self.db.execute(
            select(func.count(func.distinct(Order.conversation_id))).where(
                Order.business_id == business_id,
                Order.created_at >= start,
                Order.created_at <= end,
            ).group_by(Order.conversation_id).having(func.count(Order.id) > 1)
        )
        repeat = len(repeat_result.all())

        bc = await self._get_business_context(business_id)
        custom_stages = FunnelAdapter.get_stages(bc.business_type if bc else None)

        metric = FunnelMetric(
            business_id=business_id,
            period=period,
            period_type=period_type,
            leads_count=leads,
            qualified_count=qualified,
            deals_count=deals,
            orders_count=orders,
            repeat_orders_count=repeat,
            conversion_lead_to_qualified=Decimal(str(qualified / leads * 100)) if leads else 0,
            conversion_qualified_to_deal=Decimal(str(deals / qualified * 100)) if qualified else 0,
            conversion_deal_to_order=Decimal(str(orders / deals * 100)) if deals else 0,
            conversion_order_to_repeat=Decimal(str(repeat / orders * 100)) if orders else 0,
            revenue_total=revenue,
            avg_order_value=aov,
        )
        # Attach custom stages as extra_data for API response enrichment
        metric._custom_stages = custom_stages  # type: ignore
        self.db.add(metric)
        await self.db.commit()
        return metric

    # ========== Churn Prediction (AI-based) ==========

    async def predict_churn(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[ChurnPrediction]:
        """Generate a churn prediction for a customer using heuristics + AI."""
        result = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = result.scalar_one_or_none()
        if not conv:
            return None

        bc = await self._get_business_context(business_id)
        thresholds = ChurnAdapter.get_thresholds(bc.business_type if bc else None)
        recommended_action = ChurnAdapter.get_recommended_action(bc.business_type if bc else None)

        now = datetime.now(timezone.utc)
        factors = []

        # Inactivity
        last_msg_result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.direction == "inbound",
            ).order_by(desc(Message.created_at)).limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        days_inactive = (now - last_msg.created_at).days if last_msg else 999
        crit_inactive = thresholds["inactive_days_critical"]
        warn_inactive = thresholds["inactive_days_warning"]
        if days_inactive > crit_inactive:
            factors.append(f"inactive_{crit_inactive}_days")
        elif days_inactive > warn_inactive:
            factors.append(f"inactive_{warn_inactive}_days")

        # Competitor mentions
        if conv.extra_data and conv.extra_data.get("competitor_mentions"):
            factors.append("competitor_mentioned")

        # No orders recently
        last_order_result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == conversation_id,
                Order.is_active == True,
            ).order_by(desc(Order.created_at)).limit(1)
        )
        last_order = last_order_result.scalar_one_or_none()
        days_since_order = (now - last_order.created_at).days if last_order else 999
        no_order_crit = thresholds["no_order_days"]
        if days_since_order > no_order_crit:
            factors.append(f"no_order_{no_order_crit}_days")

        # Calculate risk
        risk_score = 0
        if days_inactive > crit_inactive: risk_score += 40
        elif days_inactive > warn_inactive: risk_score += 25
        if "competitor_mentioned" in factors: risk_score += 30
        if days_since_order > no_order_crit: risk_score += 20
        elif days_since_order > (no_order_crit // 2): risk_score += 10

        probability = min(1.0, risk_score / 100)
        if probability >= 0.8:
            risk_level = ChurnRiskLevel.CRITICAL
        elif probability >= 0.6:
            risk_level = ChurnRiskLevel.HIGH
        elif probability >= 0.4:
            risk_level = ChurnRiskLevel.MEDIUM
        else:
            risk_level = ChurnRiskLevel.LOW

        prediction = ChurnPrediction(
            business_id=business_id,
            conversation_id=conversation_id,
            risk_level=risk_level,
            churn_probability=Decimal(str(probability)),
            factors=factors,
            recommended_action=recommended_action if risk_level in (ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL) else "Monitorear",
        )
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        return prediction

    async def predict_ltv(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[LtvPrediction]:
        """Estimate LTV based on historical behavior."""
        orders_result = await self.db.execute(
            select(Order).where(
                Order.business_id == business_id,
                Order.conversation_id == conversation_id,
                Order.is_active == True,
            ).order_by(desc(Order.created_at))
        )
        orders = orders_result.scalars().all()

        if not orders:
            return None

        bc = await self._get_business_context(business_id)
        multipliers = LtvAdapter.get_multipliers(bc.business_type if bc else None)

        total_revenue = sum(o.total_amount for o in orders)
        avg_order = total_revenue / len(orders)
        days_between = []
        for i in range(1, len(orders)):
            delta = (orders[i-1].created_at - orders[i].created_at).days
            days_between.append(delta)
        avg_days_between = sum(days_between) / len(days_between) if days_between else 30

        # Predict orders in next 12 months with business-type multiplier
        predicted_orders = max(1, int(365 / avg_days_between * multipliers["predicted_orders_multiplier"]))
        predicted_ltv = avg_order * predicted_orders
        confidence = min(1.0, len(orders) / 5 + multipliers["confidence_boost"])

        factors = []
        if len(orders) >= 3: factors.append("repeat_buyer_pattern")
        if avg_order > Decimal("50000"): factors.append("high_aov")
        if avg_days_between < 30: factors.append("frequent_buyer")

        prediction = LtvPrediction(
            business_id=business_id,
            conversation_id=conversation_id,
            predicted_ltv=predicted_ltv,
            predicted_orders=predicted_orders,
            confidence_score=Decimal(str(confidence)),
            factors=factors,
        )
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        return prediction

    # ========== Insight Alerts ==========

    async def generate_insight_alert(self, business_id: uuid.UUID, insight_type: str, title: str, description: str, severity: str = "info", metric_name: Optional[str] = None, metric_change: Optional[Decimal] = None, recommended_action: Optional[str] = None) -> InsightAlert:
        alert = InsightAlert(
            business_id=business_id,
            insight_type=insight_type,
            title=title,
            description=description,
            severity=severity,
            metric_name=metric_name,
            metric_change_percent=metric_change,
            recommended_action=recommended_action,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def detect_anomalies(self, business_id: uuid.UUID):
        """Detect business anomalies and create insight alerts."""
        bc = await self._get_business_context(business_id)
        thresholds = AlertAdapter.get_revenue_thresholds(bc.business_type if bc else None)
        recommendations = AlertAdapter.get_recommendations(bc.business_type if bc else None)

        # Compare this month vs last month
        now = datetime.now(timezone.utc)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        # Revenue comparison
        this_rev_result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.business_id == business_id,
                Order.created_at >= this_month_start,
                Order.is_active == True,
            )
        )
        last_rev_result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.business_id == business_id,
                Order.created_at >= last_month_start,
                Order.created_at < this_month_start,
                Order.is_active == True,
            )
        )
        this_rev = Decimal(str(this_rev_result.scalar() or 0))
        last_rev = Decimal(str(last_rev_result.scalar() or 0))

        if last_rev > 0:
            change = ((this_rev - last_rev) / last_rev) * 100
            drop_threshold = thresholds["drop_critical"]
            growth_threshold = thresholds["growth_opportunity"]
            if change < drop_threshold:
                await self.generate_insight_alert(
                    business_id=business_id,
                    insight_type="funnel_drop",
                    title=f"Revenue bajó más de {abs(drop_threshold):.0f}% vs mes pasado",
                    description=f"Revenue este mes: ${this_rev} vs mes pasado: ${last_rev}. Revisa tus campañas activas.",
                    severity="critical",
                    metric_name="revenue",
                    metric_change=change,
                    recommended_action=recommendations["drop"],
                )
            elif change > growth_threshold:
                await self.generate_insight_alert(
                    business_id=business_id,
                    insight_type="opportunity",
                    title=f"Revenue creció más de {growth_threshold:.0f}% vs mes pasado",
                    description=f"Revenue este mes: ${this_rev} vs mes pasado: ${last_rev}. Aprovecha el momentum.",
                    severity="info",
                    metric_name="revenue",
                    metric_change=change,
                    recommended_action=recommendations["growth"],
                )

        logger.info(f"Anomaly detection completed for business {business_id}")
