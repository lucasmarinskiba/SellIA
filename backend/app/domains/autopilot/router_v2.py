"""Smart Action Router

Listens to events from the event bus and routes them to appropriate autopilot actions.
"""

import uuid
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.autopilot.service import AutopilotEngine, AutopilotExecutor, AutopilotActionType, AutopilotActionStatus
from app.domains.autopilot.models import AutopilotConfig
from app.domains.intelligence.models import MessageAnalysis
from app.domains.crm.models import Deal, LeadScore
from app.domains.channels.models import Conversation
from app.domains.retention.models import HealthScoreRecord
from app.core.logger import get_logger
from app.core.events import event_bus
from app.core.database import AsyncSessionLocal

logger = get_logger(__name__)


class SmartActionRouter:
    """Routes business events to autonomous actions based on intelligent rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.autopilot = AutopilotEngine(db)
        self.executor = AutopilotExecutor(db)

    async def route_event(self, event_type: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Main routing logic. Returns list of actions taken."""
        business_id = context.get("business_id")
        if not business_id:
            return []

        config = await self.autopilot.get_or_create_config(uuid.UUID(business_id))
        if not config.is_active or config.is_paused:
            return []

        actions = []

        # Route by event type
        if event_type == "buying_signal.detected":
            action = await self._handle_buying_signal(context, config)
            if action:
                actions.append(action)

        elif event_type == "intent.detected":
            action = await self._handle_intent(context, config)
            if action:
                actions.append(action)

        elif event_type == "objection.raised":
            action = await self._handle_objection(context, config)
            if action:
                actions.append(action)

        elif event_type == "lead_score.changed":
            action = await self._handle_lead_score_change(context, config)
            if action:
                actions.append(action)

        elif event_type == "deal.stalled":
            action = await self._handle_deal_stalled(context, config)
            if action:
                actions.append(action)

        elif event_type == "conversation.no_reply":
            action = await self._handle_no_reply(context, config)
            if action:
                actions.append(action)

        elif event_type == "health_score.declined":
            action = await self._handle_health_declined(context, config)
            if action:
                actions.append(action)

        elif event_type == "churn_risk.detected":
            action = await self._handle_churn_risk(context, config)
            if action:
                actions.append(action)

        elif event_type == "inbound.lead_captured":
            action = await self._handle_inbound_lead(context, config)
            if action:
                actions.append(action)

        elif event_type == "lead_magnet.converted":
            action = await self._handle_lead_magnet_converted(context, config)
            if action:
                actions.append(action)

        elif event_type == "referral.signup":
            action = await self._handle_referral_signup(context, config)
            if action:
                actions.append(action)

        return actions

    async def _handle_buying_signal(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """When buying signals are detected, close deal or send proposal."""
        conversation_id = uuid.UUID(context["conversation_id"])

        # Find open deal for this conversation
        from sqlalchemy import select
        result = await self.db.execute(
            select(Deal).where(
                Deal.conversation_id == conversation_id,
                Deal.is_active == True,
                Deal.stage.notin_(["closed_won", "closed_lost"]),
            )
        )
        deal = result.scalar_one_or_none()

        if deal and deal.stage in ["negotiating", "proposal_sent"]:
            # Auto-close if allowed
            can_close, reason = await self.autopilot.should_auto_execute(
                AutopilotActionType.CLOSE_DEAL,
                config.business_id,
                {"amount": float(deal.value) if deal.value else 0},
            )
            if can_close and config.auto_close_deals:
                # Close the deal
                deal.stage = "closed_won"
                from datetime import datetime, timezone
                deal.actual_close_date = datetime.now(timezone.utc)
                deal.close_reason = "Auto-closed: buying signal detected by AI"
                await self.db.commit()

                log = await self.autopilot.log_action(
                    business_id=config.business_id,
                    action_type=AutopilotActionType.CLOSE_DEAL,
                    entity_type="deal",
                    entity_id=deal.id,
                    reason="AI detected buying signals in conversation",
                    status=AutopilotActionStatus.EXECUTED,
                    context_data={"signals": context.get("signals", []), "urgency": context.get("urgency")},
                    revenue_impact=deal.value,
                )
                return {"action": "close_deal", "deal_id": str(deal.id), "log_id": str(log.id)}

        # If no deal or early stage, create deal
        if not deal and config.auto_move_deals:
            can_create, _ = await self.autopilot.should_auto_execute(
                AutopilotActionType.CREATE_DEAL, config.business_id
            )
            if can_create:
                new_deal = Deal(
                    business_id=config.business_id,
                    conversation_id=conversation_id,
                    title="Deal from hot lead",
                    stage="new_lead",
                )
                self.db.add(new_deal)
                await self.db.commit()

                log = await self.autopilot.log_action(
                    business_id=config.business_id,
                    action_type=AutopilotActionType.CREATE_DEAL,
                    entity_type="deal",
                    entity_id=new_deal.id,
                    reason="AI detected buying signals, auto-created deal",
                    status=AutopilotActionStatus.EXECUTED,
                )
                return {"action": "create_deal", "deal_id": str(new_deal.id), "log_id": str(log.id)}

        return None

    async def _handle_intent(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Route based on detected intent."""
        intent_type = context.get("intent_type")
        conversation_id = uuid.UUID(context["conversation_id"])

        if intent_type == "price_inquiry" and config.auto_send_followups:
            # Check lead score
            from sqlalchemy import select
            score_result = await self.db.execute(
                select(LeadScore).where(LeadScore.conversation_id == conversation_id)
            )
            score = score_result.scalar_one_or_none()

            if score and score.total_score >= 60:
                can_send, _ = await self.autopilot.should_auto_execute(
                    AutopilotActionType.SEND_FOLLOWUP, config.business_id
                )
                if can_send:
                    # Generate AI proposal
                    from app.domains.agents.ai_reply import generate_ai_response
                    try:
                        await generate_ai_response(
                            db=self.db,
                            business_id=config.business_id,
                            conversation_id=conversation_id,
                            message_text="El lead preguntó por precio. Enviar propuesta personalizada.",
                            personality_slug="vendedor",
                        )

                        log = await self.autopilot.log_action(
                            business_id=config.business_id,
                            action_type=AutopilotActionType.SEND_FOLLOWUP,
                            entity_type="conversation",
                            entity_id=conversation_id,
                            reason=f"Intent detected: price_inquiry (confidence: {context.get('confidence', 0)}). Lead score: {score.total_score}",
                            status=AutopilotActionStatus.EXECUTED,
                        )
                        return {"action": "send_proposal", "conversation_id": str(conversation_id), "log_id": str(log.id)}
                    except Exception as e:
                        logger.warning(f"Failed to send AI proposal: {e}")

        elif intent_type == "support" or intent_type == "complaint":
            if config.auto_escalate_to_human:
                # Escalate to human
                conv_result = await self.db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conv = conv_result.scalar_one_or_none()
                if conv:
                    conv.awaiting_human = True
                    await self.db.commit()

                log = await self.autopilot.log_action(
                    business_id=config.business_id,
                    action_type=AutopilotActionType.ESCALATE_TO_HUMAN,
                    entity_type="conversation",
                    entity_id=conversation_id,
                    reason=f"Intent detected: {intent_type}. Escalating to human agent.",
                    status=AutopilotActionStatus.EXECUTED,
                )
                return {"action": "escalate_human", "conversation_id": str(conversation_id), "log_id": str(log.id)}

        return None

    async def _handle_objection(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """When objections are raised, send counter-message via objection handler agent."""
        if not config.auto_send_followups:
            return None

        conversation_id = uuid.UUID(context["conversation_id"])
        objections = context.get("objections", [])

        can_send, _ = await self.autopilot.should_auto_execute(
            AutopilotActionType.SEND_FOLLOWUP, config.business_id
        )
        if not can_send:
            return None

        # Generate objection-handling response
        from app.domains.agents.ai_reply import generate_ai_response
        try:
            objection_text = ", ".join(objections)
            await generate_ai_response(
                db=self.db,
                business_id=config.business_id,
                conversation_id=conversation_id,
                message_text=f"El lead tiene estas objeciones: {objection_text}. Responder con empatía y valor.",
                personality_slug="vendedor",
            )

            log = await self.autopilot.log_action(
                business_id=config.business_id,
                action_type=AutopilotActionType.SEND_FOLLOWUP,
                entity_type="conversation",
                entity_id=conversation_id,
                reason=f"Objections detected: {objection_text}",
                status=AutopilotActionStatus.EXECUTED,
            )
            return {"action": "handle_objection", "conversation_id": str(conversation_id), "log_id": str(log.id)}
        except Exception as e:
            logger.warning(f"Failed to handle objection: {e}")

        return None

    async def _handle_lead_score_change(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """When lead score changes significantly, take action."""
        conversation_id = uuid.UUID(context.get("conversation_id", context.get("conversation_id")))

        # Get current score
        from sqlalchemy import select
        score_result = await self.db.execute(
            select(LeadScore).where(LeadScore.conversation_id == conversation_id)
        )
        score = score_result.scalar_one_or_none()
        if not score:
            return None

        # Warm → Hot transition without deal
        if score.classification == "hot" and config.auto_move_deals:
            deal_result = await self.db.execute(
                select(Deal).where(
                    Deal.conversation_id == conversation_id,
                    Deal.is_active == True,
                )
            )
            existing_deal = deal_result.scalar_one_or_none()
            if not existing_deal:
                can_create, _ = await self.autopilot.should_auto_execute(
                    AutopilotActionType.CREATE_DEAL, config.business_id
                )
                if can_create:
                    new_deal = Deal(
                        business_id=config.business_id,
                        conversation_id=conversation_id,
                        title="Hot lead auto-deal",
                        stage="new_lead",
                    )
                    self.db.add(new_deal)
                    await self.db.commit()

                    log = await self.autopilot.log_action(
                        business_id=config.business_id,
                        action_type=AutopilotActionType.CREATE_DEAL,
                        entity_type="deal",
                        entity_id=new_deal.id,
                        reason=f"Lead became HOT (score: {score.total_score}). Auto-created deal.",
                        status=AutopilotActionStatus.EXECUTED,
                    )
                    return {"action": "create_deal", "deal_id": str(new_deal.id), "log_id": str(log.id)}

        return None

    async def _handle_deal_stalled(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Re-activate stalled deals."""
        if not config.auto_activate_recovery_workflows:
            return None

        deal_id = context.get("deal_id")
        if not deal_id:
            return None

        log = await self.autopilot.log_action(
            business_id=config.business_id,
            action_type=AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW,
            entity_type="deal",
            entity_id=uuid.UUID(deal_id),
            reason="Deal stalled for >3 days. Activating recovery workflow.",
            status=AutopilotActionStatus.EXECUTED,
        )
        return {"action": "activate_recovery", "deal_id": deal_id, "log_id": str(log.id)}

    async def _handle_no_reply(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Send re-engagement after no reply."""
        if not config.auto_send_followups:
            return None

        conversation_id = uuid.UUID(context["conversation_id"])
        days = context.get("days", 3)

        can_send, reason = await self.autopilot.should_auto_execute(
            AutopilotActionType.SEND_FOLLOWUP, config.business_id
        )
        if not can_send:
            return None

        # Generate context-aware re-engagement
        from app.domains.agents.ai_reply import generate_ai_response
        try:
            await generate_ai_response(
                db=self.db,
                business_id=config.business_id,
                conversation_id=conversation_id,
                message_text=f"El lead no respondió en {days} días. Enviar mensaje de re-engagement sutil y valioso. No ser insistente.",
                personality_slug="vendedor",
            )

            log = await self.autopilot.log_action(
                business_id=config.business_id,
                action_type=AutopilotActionType.SEND_FOLLOWUP,
                entity_type="conversation",
                entity_id=conversation_id,
                reason=f"No reply for {days} days. Sent re-engagement message.",
                status=AutopilotActionStatus.EXECUTED,
            )
            return {"action": "re_engagement", "conversation_id": str(conversation_id), "log_id": str(log.id)}
        except Exception as e:
            logger.warning(f"Failed to send re-engagement: {e}")

        return None

    async def _handle_health_declined(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Activate recovery for declining health score."""
        if not config.auto_activate_recovery_workflows:
            return None

        conversation_id = uuid.UUID(context["conversation_id"])

        log = await self.autopilot.log_action(
            business_id=config.business_id,
            action_type=AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW,
            entity_type="conversation",
            entity_id=conversation_id,
            reason="Customer health score declined. Activating retention workflow.",
            status=AutopilotActionStatus.EXECUTED,
        )
        return {"action": "activate_retention", "conversation_id": str(conversation_id), "log_id": str(log.id)}

    async def _handle_churn_risk(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Handle churn risk detected."""
        conversation_id = uuid.UUID(context["conversation_id"])
        sentiment_score = context.get("sentiment_score", 0)

        # Critical churn risk → escalate to human
        if sentiment_score < -0.7 and config.auto_escalate_to_human:
            conv_result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = conv_result.scalar_one_or_none()
            if conv:
                conv.awaiting_human = True
                await self.db.commit()

            log = await self.autopilot.log_action(
                business_id=config.business_id,
                action_type=AutopilotActionType.ESCALATE_TO_HUMAN,
                entity_type="conversation",
                entity_id=conversation_id,
                reason=f"Critical churn risk detected (sentiment: {sentiment_score}). Immediate human escalation.",
                status=AutopilotActionStatus.ESCALATED,
            )
            return {"action": "escalate_churn", "conversation_id": str(conversation_id), "log_id": str(log.id)}

        # Medium risk → activate recovery workflow
        if config.auto_activate_recovery_workflows:
            log = await self.autopilot.log_action(
                business_id=config.business_id,
                action_type=AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW,
                entity_type="conversation",
                entity_id=conversation_id,
                reason=f"Churn risk detected (sentiment: {sentiment_score}). Activating win-back workflow.",
                status=AutopilotActionStatus.EXECUTED,
            )
            return {"action": "activate_winback", "conversation_id": str(conversation_id), "log_id": str(log.id)}

        return None

    async def _handle_inbound_lead(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Handle new inbound lead capture."""
        lead_id = context.get("lead_id")
        source_type = context.get("source_type")

        # Auto-enroll cold leads in value sequence
        if source_type in ["seo", "social_post", "lead_magnet"]:
            log = await self.autopilot.log_action(
                business_id=config.business_id,
                action_type=AutopilotActionType.SEND_FOLLOWUP,
                entity_type="inbound_lead",
                entity_id=uuid.UUID(lead_id) if lead_id else None,
                reason=f"New organic lead from {source_type}. Enrolling in value sequence.",
                status=AutopilotActionStatus.EXECUTED,
            )
            return {"action": "enroll_value_sequence", "lead_id": lead_id, "log_id": str(log.id)}
        return None

    async def _handle_lead_magnet_converted(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Handle lead magnet conversion."""
        conversation_id = context.get("conversation_id")
        log = await self.autopilot.log_action(
            business_id=config.business_id,
            action_type=AutopilotActionType.SEND_FOLLOWUP,
            entity_type="conversation",
            entity_id=uuid.UUID(conversation_id) if conversation_id else None,
            reason="Lead magnet converted. Scheduling personalized follow-up.",
            status=AutopilotActionStatus.EXECUTED,
        )
        return {"action": "schedule_followup", "conversation_id": conversation_id, "log_id": str(log.id)}

    async def _handle_referral_signup(self, context: dict, config: AutopilotConfig) -> Optional[dict]:
        """Handle new referral signup."""
        new_conversation_id = context.get("new_conversation_id")
        log = await self.autopilot.log_action(
            business_id=config.business_id,
            action_type=AutopilotActionType.SEND_WELCOME,
            entity_type="conversation",
            entity_id=uuid.UUID(new_conversation_id) if new_conversation_id else None,
            reason="New referral signup. Sending welcome sequence.",
            status=AutopilotActionStatus.EXECUTED,
        )
        return {"action": "welcome_referral", "conversation_id": new_conversation_id, "log_id": str(log.id)}


# Singleton instance for event bus subscription
_smart_router: Optional[SmartActionRouter] = None


async def init_smart_router():
    """Initialize and subscribe the smart router to event bus."""
    global _smart_router

    async with AsyncSessionLocal() as db:
        _smart_router = SmartActionRouter(db)

        # Subscribe to all relevant events
        events = [
            "message.analyzed",
            "intent.detected",
            "buying_signal.detected",
            "objection.raised",
            "lead_score.changed",
            "deal.stalled",
            "conversation.no_reply",
            "health_score.declined",
            "churn_risk.detected",
            "inbound.lead_captured",
            "lead_magnet.delivered",
            "lead_magnet.converted",
            "referral.signup",
            "social_proof.approved",
        ]

        for event in events:
            event_bus.subscribe(event, _on_event)

        logger.info("SmartActionRouter initialized and subscribed to %d events", len(events))


async def _on_event(event_type: str, payload: dict):
    """Event handler callback."""
    if not _smart_router:
        return

    try:
        # Create new DB session for each event
        async with AsyncSessionLocal() as db:
            router = SmartActionRouter(db)
            actions = await router.route_event(event_type, payload)
            if actions:
                logger.info(f"SmartActionRouter executed {len(actions)} actions for {event_type}")
    except Exception as e:
        logger.exception(f"SmartActionRouter error handling {event_type}: {e}")
