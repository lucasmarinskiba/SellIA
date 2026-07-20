"""Alert Engine

Evaluates alert rules against real-time events and scheduled checks,
generating alerts and recommendations.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.models import (
    AlertRule, AlertRuleType, AlertSeverity, AlertStatus,
    Alert, Recommendation, RecommendationType, RecommendationActionType, RecommendationStatus,
)
from app.domains.crm.models import Deal, LeadScore
from app.domains.orders.models import Order, OrderStatus
from app.domains.channels.models import Conversation


class AlertEngine:
    """Engine that evaluates alert rules and generates alerts + recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Real-time event evaluation ==========

    async def evaluate_rules(
        self,
        event_type: str,
        business_id: uuid.UUID,
        **context: Any,
    ) -> List[Alert]:
        """Evaluate all active alert rules for a business on a given event."""
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.business_id == business_id,
                AlertRule.is_active == True,
                AlertRule.rule_type == self._event_to_rule_type(event_type),
            )
        )
        rules = result.scalars().all()
        generated: List[Alert] = []

        for rule in rules:
            if await self._should_throttle(rule, business_id):
                continue
            alert = await self._evaluate_single_rule(rule, business_id, context)
            if alert:
                self.db.add(alert)
                generated.append(alert)
                # Generate recommendation linked to this alert
                rec = await self._generate_recommendation(alert, rule)
                if rec:
                    self.db.add(rec)

        if generated:
            await self.db.commit()
        return generated

    async def _evaluate_single_rule(
        self,
        rule: AlertRule,
        business_id: uuid.UUID,
        context: Dict[str, Any],
    ) -> Optional[Alert]:
        cfg = rule.config or {}
        rule_type = rule.rule_type

        if rule_type == AlertRuleType.LEAD_SCORE_THRESHOLD:
            new_score = context.get("new_score", 0)
            threshold = cfg.get("threshold", 80)
            if new_score >= threshold:
                return Alert(
                    business_id=business_id,
                    rule_id=rule.id,
                    conversation_id=uuid.UUID(context["conversation_id"]) if context.get("conversation_id") else None,
                    title=f"Lead score alcanzó {new_score}",
                    description=f"El lead superó el umbral de {threshold} puntos.",
                    severity=rule.severity,
                    entity_type="conversation",
                    entity_id=uuid.UUID(context["conversation_id"]) if context.get("conversation_id") else None,
                    alert_metadata={"new_score": new_score, "threshold": threshold},
                )

        elif rule_type == AlertRuleType.DEAL_STALLED:
            # Real-time events don't trigger this; scheduled checks do
            return None

        elif rule_type == AlertRuleType.HOT_LEAD_NO_DEAL:
            new_classification = context.get("new_classification")
            if new_classification == "hot":
                conv_id = context.get("conversation_id")
                return Alert(
                    business_id=business_id,
                    rule_id=rule.id,
                    conversation_id=uuid.UUID(conv_id) if conv_id else None,
                    title="Lead caliente sin deal",
                    description="Un lead clasificado como HOT no tiene un deal asociado.",
                    severity=AlertSeverity.WARNING,
                    entity_type="conversation",
                    entity_id=uuid.UUID(conv_id) if conv_id else None,
                )

        elif rule_type == AlertRuleType.WORKFLOW_FAILED:
            status = context.get("status")
            if status == "failed":
                return Alert(
                    business_id=business_id,
                    rule_id=rule.id,
                    title="Workflow falló",
                    description=f"La ejecución del workflow falló.",
                    severity=AlertSeverity.CRITICAL,
                    alert_metadata={"workflow_id": str(context.get("workflow_id")), "execution_id": str(context.get("execution_id"))},
                )

        elif rule_type == AlertRuleType.REVENUE_TARGET:
            total_amount = context.get("total_amount", 0)
            target = cfg.get("target_amount", 0)
            if target and total_amount >= target:
                return Alert(
                    business_id=business_id,
                    rule_id=rule.id,
                    order_id=uuid.UUID(context["order_id"]) if context.get("order_id") else None,
                    title="Meta de revenue alcanzada",
                    description=f"Se alcanzó la meta de ${target:,.2f} con una orden de ${total_amount:,.2f}.",
                    severity=AlertSeverity.INFO,
                    entity_type="order",
                    entity_id=uuid.UUID(context["order_id"]) if context.get("order_id") else None,
                    alert_metadata={"target": target, "total_amount": total_amount},
                )

        elif rule_type == AlertRuleType.NO_REPLY:
            # Real-time events don't trigger this well; scheduled checks do
            return None

        return None

    # ========== Scheduled checks ==========

    async def check_deal_stalled(self, business_id: Optional[uuid.UUID] = None) -> List[Alert]:
        """Find deals with no activity for N days."""
        days = 3
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(Deal).where(
            Deal.is_active == True,
            Deal.stage.notin_(["closed_won", "closed_lost"]),
            Deal.updated_at < since,
        )
        if business_id:
            query = query.where(Deal.business_id == business_id)

        result = await self.db.execute(query)
        deals = result.scalars().all()
        generated: List[Alert] = []

        for deal in deals:
            # Check if there's an active rule
            rule_result = await self.db.execute(
                select(AlertRule).where(
                    AlertRule.business_id == deal.business_id,
                    AlertRule.is_active == True,
                    AlertRule.rule_type == AlertRuleType.DEAL_STALLED,
                )
            )
            rule = rule_result.scalar_one_or_none()
            if not rule:
                continue
            if await self._should_throttle(rule, deal.business_id):
                continue

            alert = Alert(
                business_id=deal.business_id,
                rule_id=rule.id,
                deal_id=deal.id,
                title=f"Deal estancado: {deal.title or 'Sin título'}",
                description=f"Sin actividad por más de {days} días.",
                severity=AlertSeverity.WARNING,
                entity_type="deal",
                entity_id=deal.id,
                alert_metadata={"days_stalled": days, "stage": deal.stage},
            )
            self.db.add(alert)
            generated.append(alert)
            rec = await self._generate_recommendation(alert, rule)
            if rec:
                self.db.add(rec)

        if generated:
            await self.db.commit()
        return generated

    async def check_hot_leads_no_deal(self, business_id: Optional[uuid.UUID] = None) -> List[Alert]:
        """Find hot leads without an active deal."""
        query = select(LeadScore).where(
            LeadScore.classification == "hot",
        )
        if business_id:
            query = query.where(LeadScore.business_id == business_id)

        result = await self.db.execute(query)
        lead_scores = result.scalars().all()
        generated: List[Alert] = []

        for ls in lead_scores:
            # Check if already has active deal
            deal_result = await self.db.execute(
                select(Deal).where(
                    Deal.conversation_id == ls.conversation_id,
                    Deal.is_active == True,
                )
            )
            if deal_result.scalar_one_or_none():
                continue

            rule_result = await self.db.execute(
                select(AlertRule).where(
                    AlertRule.business_id == ls.business_id,
                    AlertRule.is_active == True,
                    AlertRule.rule_type == AlertRuleType.HOT_LEAD_NO_DEAL,
                )
            )
            rule = rule_result.scalar_one_or_none()
            if not rule:
                continue
            if await self._should_throttle(rule, ls.business_id):
                continue

            alert = Alert(
                business_id=ls.business_id,
                rule_id=rule.id,
                conversation_id=ls.conversation_id,
                title="Lead caliente sin deal",
                description=f"Lead con score {ls.total_score} está clasificado como HOT pero no tiene deal.",
                severity=AlertSeverity.WARNING,
                entity_type="conversation",
                entity_id=ls.conversation_id,
                alert_metadata={"total_score": ls.total_score},
            )
            self.db.add(alert)
            generated.append(alert)
            rec = await self._generate_recommendation(alert, rule)
            if rec:
                self.db.add(rec)

        if generated:
            await self.db.commit()
        return generated

    async def check_abandoned_carts(self, business_id: Optional[uuid.UUID] = None) -> List[Alert]:
        """Find pending orders older than N days."""
        days = 2
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(Order).where(
            Order.is_active == True,
            Order.status == OrderStatus.PENDING,
            Order.created_at < since,
        )
        if business_id:
            query = query.where(Order.business_id == business_id)

        result = await self.db.execute(query)
        orders = result.scalars().all()
        generated: List[Alert] = []

        for order in orders:
            rule_result = await self.db.execute(
                select(AlertRule).where(
                    AlertRule.business_id == order.business_id,
                    AlertRule.is_active == True,
                    AlertRule.rule_type == AlertRuleType.CART_ABANDONED,
                )
            )
            rule = rule_result.scalar_one_or_none()
            if not rule:
                continue
            if await self._should_throttle(rule, order.business_id):
                continue

            alert = Alert(
                business_id=order.business_id,
                rule_id=rule.id,
                order_id=order.id,
                title="Carrito abandonado",
                description=f"Orden pendiente de ${float(order.total_amount):,.2f} sin actividad por {days} días.",
                severity=AlertSeverity.INFO,
                entity_type="order",
                entity_id=order.id,
                alert_metadata={"total_amount": float(order.total_amount), "days_pending": days},
            )
            self.db.add(alert)
            generated.append(alert)
            rec = await self._generate_recommendation(alert, rule)
            if rec:
                self.db.add(rec)

        if generated:
            await self.db.commit()
        return generated

    async def check_no_reply(self, business_id: Optional[uuid.UUID] = None) -> List[Alert]:
        """Find conversations with no reply for N hours."""
        hours = 24
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(Conversation).where(
            Conversation.status == "active",
            Conversation.last_message_at < since,
        )
        if business_id:
            query = query.where(Conversation.business_id == business_id)

        result = await self.db.execute(query)
        conversations = result.scalars().all()
        generated: List[Alert] = []

        for conv in conversations:
            rule_result = await self.db.execute(
                select(AlertRule).where(
                    AlertRule.business_id == conv.business_id,
                    AlertRule.is_active == True,
                    AlertRule.rule_type == AlertRuleType.NO_REPLY,
                )
            )
            rule = rule_result.scalar_one_or_none()
            if not rule:
                continue
            if await self._should_throttle(rule, conv.business_id):
                continue

            alert = Alert(
                business_id=conv.business_id,
                rule_id=rule.id,
                conversation_id=conv.id,
                title="Conversación sin respuesta",
                description=f"Sin actividad por más de {hours} horas.",
                severity=AlertSeverity.INFO,
                entity_type="conversation",
                entity_id=conv.id,
                alert_metadata={"hours_without_reply": hours},
            )
            self.db.add(alert)
            generated.append(alert)
            rec = await self._generate_recommendation(alert, rule)
            if rec:
                self.db.add(rec)

        if generated:
            await self.db.commit()
        return generated

    # ========== Recommendation generation ==========

    async def _generate_recommendation(self, alert: Alert, rule: AlertRule) -> Optional[Recommendation]:
        """Generate a deterministic recommendation based on alert type."""
        rule_type = rule.rule_type

        if rule_type == AlertRuleType.LEAD_SCORE_THRESHOLD:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.SCORE_INCREASE,
                title="Enviar follow-up al lead caliente",
                description="El lead alcanzó un score alto. Es momento de contactarlo con una propuesta.",
                priority=4,
                action_type=RecommendationActionType.SEND_MESSAGE,
                action_payload={"template": "follow_up_hot", "conversation_id": str(alert.conversation_id) if alert.conversation_id else None},
                context_data={"alert_id": str(alert.id), "score": alert.alert_metadata.get("new_score")},
            )

        elif rule_type == AlertRuleType.DEAL_STALLED:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.DEAL_MOVE,
                title="Mover deal a nurture o enviar mensaje",
                description="El deal está estancado. Considera reactivarlo con un mensaje o moverlo a nurture.",
                priority=3,
                action_type=RecommendationActionType.SEND_MESSAGE,
                action_payload={"deal_id": str(alert.deal_id) if alert.deal_id else None},
                context_data={"alert_id": str(alert.id), "days_stalled": alert.alert_metadata.get("days_stalled")},
            )

        elif rule_type == AlertRuleType.HOT_LEAD_NO_DEAL:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.FOLLOW_UP,
                title="Crear deal para lead caliente",
                description="Este lead caliente no tiene un deal asociado. Crear uno aumentará el tracking.",
                priority=5,
                action_type=RecommendationActionType.CREATE_DEAL,
                action_payload={"conversation_id": str(alert.conversation_id) if alert.conversation_id else None},
                context_data={"alert_id": str(alert.id)},
            )

        elif rule_type == AlertRuleType.CART_ABANDONED:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.FOLLOW_UP,
                title="Enviar recordatorio de carrito abandonado",
                description="El cliente dejó una orden pendiente. Un mensaje de seguimiento puede recuperarla.",
                priority=3,
                action_type=RecommendationActionType.SEND_MESSAGE,
                action_payload={"order_id": str(alert.order_id) if alert.order_id else None, "offer_discount": True},
                context_data={"alert_id": str(alert.id), "order_amount": alert.alert_metadata.get("total_amount")},
            )

        elif rule_type == AlertRuleType.WORKFLOW_FAILED:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.CUSTOM,
                title="Revisar workflow fallido",
                description="Un workflow falló. Revisá los logs y corregí la configuración.",
                priority=5,
                action_type=RecommendationActionType.DISMISS,
                action_payload={},
                context_data={"alert_id": str(alert.id), "workflow_id": alert.alert_metadata.get("workflow_id")},
            )

        elif rule_type == AlertRuleType.NO_REPLY:
            return Recommendation(
                business_id=alert.business_id,
                type=RecommendationType.ASSIGN_AGENT,
                title="Asignar agente a conversación inactiva",
                description="Esta conversación lleva tiempo sin respuesta. Un agente humano puede reactivarla.",
                priority=2,
                action_type=RecommendationActionType.ASSIGN_AGENT,
                action_payload={"conversation_id": str(alert.conversation_id) if alert.conversation_id else None},
                context_data={"alert_id": str(alert.id)},
            )

        return None

    # ========== Throttling ==========

    async def _should_throttle(self, rule: AlertRule, business_id: uuid.UUID) -> bool:
        """Check cooldown and max alerts per day."""
        # Cooldown
        cooldown_since = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
        from app.domains.alerts.models import Alert
        result = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.rule_id == rule.id,
                Alert.created_at >= cooldown_since,
            )
        )
        if result.scalar() > 0:
            return True

        # Max per day
        day_since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.rule_id == rule.id,
                Alert.created_at >= day_since,
            )
        )
        if result.scalar() >= rule.max_alerts_per_day:
            return True

        return False

    # ========== Helpers ==========

    @staticmethod
    def _event_to_rule_type(event_type: str) -> Optional[AlertRuleType]:
        mapping = {
            "lead.score_changed": AlertRuleType.LEAD_SCORE_THRESHOLD,
            "deal.created": AlertRuleType.DEAL_STALLED,
            "order.created": AlertRuleType.REVENUE_TARGET,
            "workflow.completed": AlertRuleType.WORKFLOW_FAILED,
            "human.handoff_required": AlertRuleType.NO_REPLY,
        }
        return mapping.get(event_type)
