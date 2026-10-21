"""Alert Service

CRUD operations and business logic for alerts, rules, and recommendations.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.models import (
    Alert,
    AlertRule,
    AlertStatus,
    Recommendation,
    RecommendationStatus,
)
from app.domains.alerts.schemas import (
    AlertRuleCreate,
    AlertRuleUpdate,
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

    async def list_rules(self, business_id: uuid.UUID) -> list[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.business_id == business_id,
                AlertRule.is_active == True,
            ).order_by(desc(AlertRule.created_at))
        )
        return result.scalars().all()

    async def get_rule(self, rule_id: uuid.UUID) -> AlertRule | None:
        result = await self.db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        return result.scalar_one_or_none()

    async def update_rule(self, rule_id: uuid.UUID, data: AlertRuleUpdate) -> AlertRule | None:
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
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        query = select(Alert).where(Alert.business_id == business_id)
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)
        query = query.order_by(desc(Alert.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_alert(self, alert_id: uuid.UUID) -> Alert | None:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def mark_read(self, alert_id: uuid.UUID) -> Alert | None:
        alert = await self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.READ
        alert.read_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def dismiss_alert(self, alert_id: uuid.UUID) -> Alert | None:
        alert = await self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.DISMISSED
        alert.dismissed_at = datetime.now(UTC)
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

    async def get_stats(self, business_id: uuid.UUID) -> dict[str, Any]:
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
        status: str | None = "pending",
        limit: int = 100,
    ) -> list[Recommendation]:
        query = select(Recommendation).where(Recommendation.business_id == business_id)
        if status:
            query = query.where(Recommendation.status == status)
        query = query.order_by(desc(Recommendation.priority), desc(Recommendation.created_at)).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recommendation(self, rec_id: uuid.UUID) -> Recommendation | None:
        result = await self.db.execute(select(Recommendation).where(Recommendation.id == rec_id))
        return result.scalar_one_or_none()

    async def apply_recommendation(
        self,
        rec_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> Recommendation | None:
        rec = await self.get_recommendation(rec_id)
        if not rec:
            return None
        if rec.status != RecommendationStatus.PENDING:
            return rec  # already answered: applying twice must not act twice
        from app.domains.channels.token_rotation import (
            apply_rotation,
            is_rotation_proposal,
        )

        if is_rotation_proposal(rec):
            await apply_rotation(self.db, rec, user_id)  # raises RotationNotPossible
        else:
            rec.status = RecommendationStatus.APPLIED
            rec.applied_at = datetime.now(UTC)
            rec.applied_by_user_id = user_id
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def dismiss_recommendation(self, rec_id: uuid.UUID) -> Recommendation | None:
        rec = await self.get_recommendation(rec_id)
        if not rec:
            return None
        if rec.status != RecommendationStatus.PENDING:
            return rec
        rec.status = RecommendationStatus.DISMISSED
        await self.db.commit()
        await self.db.refresh(rec)
        return rec
