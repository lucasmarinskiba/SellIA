"""Alert Service

CRUD operations and business logic for alerts, rules, and recommendations.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.models import (
    AlertRule, Alert, Recommendation,
    AlertStatus, RecommendationStatus,
)
from app.domains.alerts.schemas import (
    AlertRuleCreate, AlertRuleUpdate,
    RecommendationApplyRequest,
)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Alert Rules ==========

    async def create_rule(self, data: AlertRuleCreate) -> AlertRule:
        rule = AlertRule(**data.model_dump())
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_rules(self, business_id: uuid.UUID) -> List[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.business_id == business_id,
                AlertRule.is_active == True,
            ).order_by(desc(AlertRule.created_at))
        )
        return result.scalars().all()

    async def get_rule(self, rule_id: uuid.UUID) -> Optional[AlertRule]:
        result = await self.db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        return result.scalar_one_or_none()

    async def update_rule(self, rule_id: uuid.UUID, data: AlertRuleUpdate) -> Optional[AlertRule]:
        rule = await self.get_rule(rule_id)
        if not rule:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        rule = await self.get_rule(rule_id)
        if not rule:
            return False
        rule.is_active = False
        await self.db.commit()
        return True

    # ========== Alerts ==========

    async def list_alerts(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Alert]:
        query = select(Alert).where(Alert.business_id == business_id)
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)
        query = query.order_by(desc(Alert.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_alert(self, alert_id: uuid.UUID) -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def mark_read(self, alert_id: uuid.UUID) -> Optional[Alert]:
        alert = await self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.READ
        alert.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def dismiss_alert(self, alert_id: uuid.UUID) -> Optional[Alert]:
        alert = await self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.DISMISSED
        alert.dismissed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def delete_alert(self, alert_id: uuid.UUID) -> bool:
        alert = await self.get_alert(alert_id)
        if not alert:
            return False
        await self.db.delete(alert)
        await self.db.commit()
        return True

    async def get_stats(self, business_id: uuid.UUID) -> Dict[str, Any]:
        unread = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.business_id == business_id, Alert.status == AlertStatus.UNREAD
            )
        )
        read = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.business_id == business_id, Alert.status == AlertStatus.READ
            )
        )
        dismissed = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.business_id == business_id, Alert.status == AlertStatus.DISMISSED
            )
        )
        by_severity = {}
        for sev in ["info", "warning", "critical"]:
            cnt = await self.db.execute(
                select(func.count(Alert.id)).where(
                    Alert.business_id == business_id,
                    Alert.status == AlertStatus.UNREAD,
                    Alert.severity == sev,
                )
            )
            by_severity[sev] = cnt.scalar()

        return {
            "total_unread": unread.scalar(),
            "total_read": read.scalar(),
            "total_dismissed": dismissed.scalar(),
            "by_severity": by_severity,
        }

    # ========== Recommendations ==========

    async def list_recommendations(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = "pending",
        limit: int = 100,
    ) -> List[Recommendation]:
        query = select(Recommendation).where(Recommendation.business_id == business_id)
        if status:
            query = query.where(Recommendation.status == status)
        query = query.order_by(desc(Recommendation.priority), desc(Recommendation.created_at)).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recommendation(self, rec_id: uuid.UUID) -> Optional[Recommendation]:
        result = await self.db.execute(select(Recommendation).where(Recommendation.id == rec_id))
        return result.scalar_one_or_none()

    async def apply_recommendation(
        self,
        rec_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Recommendation]:
        rec = await self.get_recommendation(rec_id)
        if not rec:
            return None
        rec.status = RecommendationStatus.APPLIED
        rec.applied_at = datetime.now(timezone.utc)
        rec.applied_by_user_id = user_id
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def dismiss_recommendation(self, rec_id: uuid.UUID) -> Optional[Recommendation]:
        rec = await self.get_recommendation(rec_id)
        if not rec:
            return None
        rec.status = RecommendationStatus.DISMISSED
        await self.db.commit()
        await self.db.refresh(rec)
        return rec
