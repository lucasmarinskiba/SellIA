"""Objectives & KPIs Services.

Tracks goals, calculates progress, and links to workflows/agents.
"""

import uuid
from typing import Any, Optional
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.objectives.models import Department, BusinessObjective, KPI, KeyResult, ObjectiveStatus, ObjectivePeriod
from app.domains.businesses.models import Business
from app.core.logger import get_logger

logger = get_logger(__name__)


class ObjectiveService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_department(self, business_id: uuid.UUID, name: str, slug: str, **kwargs) -> Department:
        dept = Department(business_id=business_id, name=name, slug=slug, **kwargs)
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def create_objective(self, business_id: uuid.UUID, name: str, target_value: Decimal, start_date: datetime, end_date: datetime, **kwargs) -> BusinessObjective:
        obj = BusinessObjective(
            business_id=business_id,
            name=name,
            target_value=target_value,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def create_kpi(self, business_id: uuid.UUID, name: str, slug: str, metric_type: str, data_source: str, **kwargs) -> KPI:
        kpi = KPI(business_id=business_id, name=name, slug=slug, metric_type=metric_type, data_source=data_source, **kwargs)
        self.db.add(kpi)
        await self.db.commit()
        await self.db.refresh(kpi)
        return kpi

    async def get_objectives_for_business(self, business_id: uuid.UUID, status: Optional[str] = None):
        query = select(BusinessObjective).where(BusinessObjective.business_id == business_id, BusinessObjective.is_active == True)
        if status:
            query = query.where(BusinessObjective.status == ObjectiveStatus(status))
        result = await self.db.execute(query.order_by(desc(BusinessObjective.created_at)))
        return result.scalars().all()

    async def get_kpis_for_business(self, business_id: uuid.UUID, period: Optional[str] = None):
        query = select(KPI).where(KPI.business_id == business_id, KPI.is_active == True)
        if period:
            query = query.where(KPI.period == ObjectivePeriod(period))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_objective_progress(self, objective_id: uuid.UUID, delta_value: Decimal):
        """Increment current_value of an objective (called by workflows/events)."""
        result = await self.db.execute(select(BusinessObjective).where(BusinessObjective.id == objective_id))
        obj = result.scalar_one_or_none()
        if not obj:
            return
        obj.current_value = (obj.current_value or Decimal("0")) + delta_value
        progress = obj.current_value / obj.target_value if obj.target_value else 0
        if progress >= 1:
            obj.status = ObjectiveStatus.ACHIEVED
        elif progress < (obj.alert_threshold_percent or 80) / 100:
            obj.status = ObjectiveStatus.AT_RISK
        await self.db.commit()

    async def calculate_kpi_value(self, kpi: KPI) -> Decimal:
        """Calculate the current value of a KPI from its data source."""
        from app.domains.orders.models import Order
        from app.domains.channels.models import Conversation, Message
        from app.domains.crm.models import Deal

        filter_config = kpi.data_source_filter or {}
        platform = filter_config.get("platform")
        status = filter_config.get("status")

        if kpi.data_source == "orders":
            query = select(func.sum(Order.total_amount)).where(
                Order.business_id == kpi.business_id,
                Order.is_active == True,
            )
            if platform:
                query = query.where(Order.source_channel == platform)
            if status:
                query = query.where(Order.status == status)
            if kpi.period_start and kpi.period_end:
                query = query.where(Order.created_at >= kpi.period_start, Order.created_at <= kpi.period_end)
            result = await self.db.execute(query)
            return Decimal(str(result.scalar() or 0))

        elif kpi.data_source == "conversations":
            query = select(func.count(Conversation.id)).where(
                Conversation.business_id == kpi.business_id,
                Conversation.is_active == True,
            )
            if platform:
                query = query.where(Conversation.lead_source == platform)
            if kpi.period_start and kpi.period_end:
                query = query.where(Conversation.created_at >= kpi.period_start, Conversation.created_at <= kpi.period_end)
            result = await self.db.execute(query)
            return Decimal(str(result.scalar() or 0))

        elif kpi.data_source == "deals":
            query = select(func.sum(Deal.value)).where(
                Deal.business_id == kpi.business_id,
                Deal.is_active == True,
            )
            if status:
                query = query.where(Deal.stage == status)
            if kpi.period_start and kpi.period_end:
                query = query.where(Deal.created_at >= kpi.period_start, Deal.created_at <= kpi.period_end)
            result = await self.db.execute(query)
            return Decimal(str(result.scalar() or 0))

        return Decimal("0")

    async def refresh_all_kpis(self, business_id: uuid.UUID):
        """Recalculate all active KPIs for a business. Called by Celery beat."""
        result = await self.db.execute(select(KPI).where(KPI.business_id == business_id, KPI.is_active == True))
        kpis = result.scalars().all()
        for kpi in kpis:
            try:
                kpi.current_value = await self.calculate_kpi_value(kpi)
            except Exception as e:
                logger.error(f"KPI refresh error {kpi.slug}: {e}")
        await self.db.commit()
        logger.info(f"Refreshed {len(kpis)} KPIs for business {business_id}")
