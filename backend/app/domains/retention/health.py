"""Customer Health Score & Churn Prevention Engine.

Detects at-risk customers BEFORE they churn and activates retention workflows.
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.retention.models import CustomerSegment, CustomerSegmentType
from app.domains.channels.models import Conversation, Message
from app.domains.orders.models import Order
from app.domains.retention.models import NpsResponse
from app.domains.support.models import SupportTicket
from app.core.logger import get_logger

logger = get_logger(__name__)


class ChurnRiskLevel(str):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerHealthScore:
    """In-memory health score calculation."""

    def __init__(
        self,
        conversation_id: uuid.UUID,
        health_score: int = 100,
        trend: str = "stable",
        churn_risk_level: str = ChurnRiskLevel.NONE,
        recommended_action: str = "",
    ):
        self.conversation_id = conversation_id
        self.health_score = health_score
        self.trend = trend
        self.churn_risk_level = churn_risk_level
        self.recommended_action = recommended_action


class HealthScoringService:
    """Calculates customer health scores for churn prevention."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_health_for_conversation(self, conversation_id: uuid.UUID) -> CustomerHealthScore:
        """Calculate health score for a single customer."""
        # Get conversation
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            return CustomerHealthScore(conversation_id, 0, "declining", ChurnRiskLevel.CRITICAL, "Cliente no encontrado")

        business_id = conv.business_id
        now = datetime.now(timezone.utc)

        # 1. Recency (30%): days since last order
        order_result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == conversation_id,
                Order.is_active == True,
                Order.status.in_(["paid", "delivered"]),
            ).order_by(desc(Order.created_at)).limit(1)
        )
        last_order = order_result.scalar_one_or_none()

        if last_order and last_order.created_at:
            days_since_order = (now - last_order.created_at).days
        else:
            days_since_order = 999

        # Recency score: 0-100 (lower days = higher score)
        if days_since_order <= 7:
            recency_score = 100
        elif days_since_order <= 30:
            recency_score = 80
        elif days_since_order <= 60:
            recency_score = 60
        elif days_since_order <= 90:
            recency_score = 40
        elif days_since_order <= 180:
            recency_score = 20
        else:
            recency_score = 0

        # 2. Engagement (25%): message activity
        month_ago = now - timedelta(days=30)
        msg_result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.created_at >= month_ago,
                Message.direction == "inbound",
            )
        )
        inbound_messages = msg_result.scalar() or 0

        if inbound_messages >= 10:
            engagement_score = 100
        elif inbound_messages >= 5:
            engagement_score = 75
        elif inbound_messages >= 2:
            engagement_score = 50
        elif inbound_messages >= 1:
            engagement_score = 25
        else:
            engagement_score = 0

        # 3. NPS (25%): latest NPS response
        nps_result = await self.db.execute(
            select(NpsResponse).where(
                NpsResponse.conversation_id == conversation_id,
            ).order_by(desc(NpsResponse.created_at)).limit(1)
        )
        nps = nps_result.scalar_one_or_none()

        if nps:
            # Map 0-10 to 0-100
            nps_score = nps.score * 10
        else:
            nps_score = 50  # Neutral if no NPS yet

        # 4. Support tickets (20%): negative if many open tickets
        ticket_result = await self.db.execute(
            select(func.count(SupportTicket.id)).where(
                SupportTicket.conversation_id == conversation_id,
                SupportTicket.status.in_(["open", "pending"]),
            )
        )
        open_tickets = ticket_result.scalar() or 0

        if open_tickets == 0:
            support_score = 100
        elif open_tickets == 1:
            support_score = 70
        elif open_tickets == 2:
            support_score = 40
        else:
            support_score = 10

        # Weighted total
        health_score = int(
            recency_score * 0.30 +
            engagement_score * 0.25 +
            nps_score * 0.25 +
            support_score * 0.20
        )

        # Determine trend (compare with previous if exists)
        from app.domains.retention.models import HealthScoreHistory
        prev_result = await self.db.execute(
            select(HealthScoreHistory).where(
                HealthScoreHistory.conversation_id == conversation_id,
            ).order_by(desc(HealthScoreHistory.calculated_at)).limit(1)
        )
        prev = prev_result.scalar_one_or_none()

        if prev:
            if health_score > prev.health_score + 5:
                trend = "improving"
            elif health_score < prev.health_score - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine risk level
        if health_score >= 80:
            risk = ChurnRiskLevel.NONE
            action = "Mantener engagement. Cliente saludable."
        elif health_score >= 60:
            risk = ChurnRiskLevel.LOW
            action = "Enviar contenido de valor. Recomendar productos complementarios."
        elif health_score >= 40:
            risk = ChurnRiskLevel.MEDIUM
            action = "Activar workflow de win-back con oferta personalizada."
        elif health_score >= 20:
            risk = ChurnRiskLevel.HIGH
            action = "Alerta a owner. Oferta agresiva + contacto personal."
        else:
            risk = ChurnRiskLevel.CRITICAL
            action = "Escalar a humano inmediatamente. Riesgo crítico de churn."

        return CustomerHealthScore(
            conversation_id=conversation_id,
            health_score=health_score,
            trend=trend,
            churn_risk_level=risk,
            recommended_action=action,
        )

    async def recalculate_all_health_scores(self, business_id: uuid.UUID) -> int:
        """Recalculate health scores for all customers of a business."""
        from app.domains.retention.models import HealthScoreHistory, HealthScoreRecord

        # Get all conversations with orders
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.business_id == business_id,
                Conversation.is_active == True,
            )
        )
        conversations = result.scalars().all()

        count = 0
        for conv in conversations:
            health = await self.calculate_health_for_conversation(conv.id)

            # Upsert health score record
            record_result = await self.db.execute(
                select(HealthScoreRecord).where(
                    HealthScoreRecord.conversation_id == conv.id,
                )
            )
            record = record_result.scalar_one_or_none()
            if not record:
                record = HealthScoreRecord(
                    business_id=business_id,
                    conversation_id=conv.id,
                )
                self.db.add(record)

            record.health_score = health.health_score
            record.trend = health.trend
            record.churn_risk_level = health.churn_risk_level
            record.recommended_action = health.recommended_action
            record.last_order_days = self._get_last_order_days(conv.id)
            record.engagement_score = self._get_engagement_score(conv.id)
            record.nps_score = self._get_nps_score(conv.id)
            record.support_ticket_count = self._get_support_ticket_count(conv.id)
            record.calculated_at = datetime.now(timezone.utc)

            # Save history
            history = HealthScoreHistory(
                business_id=business_id,
                conversation_id=conv.id,
                health_score=health.health_score,
                trend=health.trend,
                churn_risk_level=health.churn_risk_level,
            )
            self.db.add(history)

            count += 1

        await self.db.commit()
        logger.info(f"Recalculated health scores for {count} customers in business {business_id}")
        return count

    def _get_last_order_days(self, conversation_id: uuid.UUID) -> int:
        # Placeholder — would be async in real implementation
        return 0

    def _get_engagement_score(self, conversation_id: uuid.UUID) -> int:
        return 0

    def _get_nps_score(self, conversation_id: uuid.UUID) -> int | None:
        return None

    def _get_support_ticket_count(self, conversation_id: uuid.UUID) -> int:
        return 0


class ChurnPreventionEngine:
    """Activates retention workflows for at-risk customers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def activate_prevention_for_business(self, business_id: uuid.UUID) -> list[dict[str, Any]]:
        """Activate churn prevention for all at-risk customers of a business."""
        from app.domains.retention.models import HealthScoreRecord
        from app.domains.autopilot.service import AutopilotEngine, AutopilotActionType, AutopilotActionStatus

        result = await self.db.execute(
            select(HealthScoreRecord).where(
                HealthScoreRecord.business_id == business_id,
                HealthScoreRecord.churn_risk_level.in_(["medium", "high", "critical"]),
            )
        )
        at_risk = result.scalars().all()

        actions = []
        for record in at_risk:
            action = await self._activate_for_customer(record)
            if action:
                actions.append(action)

        return actions

    async def _activate_for_customer(self, record) -> Optional[dict[str, Any]]:
        """Activate the appropriate retention action for a customer."""
        from app.domains.autopilot.service import AutopilotEngine, AutopilotActionType, AutopilotActionStatus

        autopilot = AutopilotEngine(self.db)
        config = await autopilot.get_or_create_config(record.business_id)

        if not config.is_active or config.is_paused:
            return None

        if record.churn_risk_level == "critical":
            # Always escalate critical
            if config.auto_escalate_to_human:
                await autopilot.log_action(
                    business_id=record.business_id,
                    action_type=AutopilotActionType.ESCALATE_TO_HUMAN,
                    entity_type="conversation",
                    entity_id=record.conversation_id,
                    reason=f"Churn risk CRITICAL. Health score: {record.health_score}. Action: {record.recommended_action}",
                    status=AutopilotActionStatus.ESCALATED,
                    context_data={"health_score": record.health_score, "trend": record.trend},
                )
                return {"conversation_id": str(record.conversation_id), "action": "escalated", "reason": "critical churn risk"}
            return None

        elif record.churn_risk_level == "high":
            if not config.auto_activate_recovery_workflows:
                return None
            # Activate aggressive win-back workflow
            return await self._trigger_workflow(record, "churn_prevention_high")

        elif record.churn_risk_level == "medium":
            if not config.auto_activate_recovery_workflows:
                return None
            # Activate gentle win-back workflow
            return await self._trigger_workflow(record, "churn_prevention_medium")

        return None

    async def _trigger_workflow(self, record, workflow_type: str) -> dict[str, Any]:
        """Trigger a retention workflow for a customer."""
        from app.domains.autopilot.service import AutopilotEngine, AutopilotActionType, AutopilotActionStatus

        autopilot = AutopilotEngine(self.db)

        # Log action
        await autopilot.log_action(
            business_id=record.business_id,
            action_type=AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW,
            entity_type="conversation",
            entity_id=record.conversation_id,
            reason=f"Churn risk {record.churn_risk_level}. Activated {workflow_type} workflow.",
            status=AutopilotActionStatus.EXECUTED,
            context_data={"workflow_type": workflow_type, "health_score": record.health_score},
        )

        # In a real implementation, this would trigger an actual workflow
        # For now, we log it and return
        logger.info(f"Activated {workflow_type} for conversation {record.conversation_id}")

        return {
            "conversation_id": str(record.conversation_id),
            "action": "workflow_activated",
            "workflow_type": workflow_type,
            "health_score": record.health_score,
        }
