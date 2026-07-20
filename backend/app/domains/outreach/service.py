"""Outreach Cadence Services.

FatigueScoringService — calculates contact fatigue in real time.
CadenceEngine — orchestrates smart follow-up sequences.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.outreach.models import (
    ContactFatigueScore,
    OutreachCadenceRule,
    OutreachLog,
    OutreachLogStatus,
    FatigueLevel,
)
from app.domains.channels.models import Conversation, Message
from app.domains.crm.models import LeadScore
from app.core.logger import get_logger

logger = get_logger(__name__)


class FatigueScoringService:
    """Calculates and enforces contact fatigue limits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_rule(self, business_id: uuid.UUID) -> OutreachCadenceRule:
        """Get or create default cadence rules for a business."""
        result = await self.db.execute(
            select(OutreachCadenceRule).where(OutreachCadenceRule.business_id == business_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            rule = OutreachCadenceRule(business_id=business_id)
            self.db.add(rule)
            await self.db.commit()
            await self.db.refresh(rule)
            logger.info(f"Created default OutreachCadenceRule for business {business_id}")
        return rule

    async def get_or_create_score(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> ContactFatigueScore:
        """Get or create fatigue score for a conversation."""
        result = await self.db.execute(
            select(ContactFatigueScore).where(
                ContactFatigueScore.business_id == business_id,
                ContactFatigueScore.conversation_id == conversation_id,
            )
        )
        score = result.scalar_one_or_none()
        if not score:
            score = ContactFatigueScore(business_id=business_id, conversation_id=conversation_id)
            self.db.add(score)
            await self.db.commit()
            await self.db.refresh(score)
        return score

    async def can_contact_now(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        channel: str | None = None,
        message_type: str | None = None,
    ) -> dict[str, Any]:
        """Check if we can contact a lead now. Returns decision dict."""
        rule = await self.get_or_create_rule(business_id)
        score = await self.get_or_create_score(business_id, conversation_id)

        # Check if autopilot is active
        from app.domains.autopilot.service import AutopilotEngine
        autopilot = AutopilotEngine(self.db)
        config = await autopilot.get_or_create_config(business_id)

        if not config.is_active or config.is_paused:
            return {
                "can_contact": False,
                "reason": "Autopilot is not active or is paused.",
                "recommended_channel": None,
                "recommended_wait_hours": None,
                "fatigue_level": score.fatigue_level,
                "contacts_this_week": score.total_contacts_last_7d,
                "ai_recommendation": None,
            }

        # Check cooldown
        if score.recommended_cooldown_until and datetime.now(timezone.utc) < score.recommended_cooldown_until:
            hours_left = int((score.recommended_cooldown_until - datetime.now(timezone.utc)).total_seconds() / 3600)
            return {
                "can_contact": False,
                "reason": f"Lead is in cooldown. Wait {hours_left} more hours.",
                "recommended_channel": None,
                "recommended_wait_hours": hours_left,
                "fatigue_level": score.fatigue_level,
                "contacts_this_week": score.total_contacts_last_7d,
                "ai_recommendation": score.ai_recommendation or f"Esperar {hours_left}h antes de contactar de nuevo.",
            }

        # Check weekly limit
        is_hot = await self._is_hot_lead(conversation_id)
        max_weekly = rule.hot_lead_max_per_week if (is_hot and rule.hot_lead_override) else rule.max_messages_per_week

        if score.total_contacts_last_7d >= max_weekly:
            return {
                "can_contact": False,
                "reason": f"Weekly contact limit reached ({score.total_contacts_last_7d}/{max_weekly}).",
                "recommended_channel": None,
                "recommended_wait_hours": 48,
                "fatigue_level": FatigueLevel.EXHAUSTED,
                "contacts_this_week": score.total_contacts_last_7d,
                "ai_recommendation": f"Límite semanal alcanzado. Esperar hasta la próxima semana.",
            }

        # Check channel-specific limit
        if channel:
            channel_count = score.contacts_by_channel.get(channel, 0)
            max_channel = rule.max_messages_per_channel_per_week
            if channel_count >= max_channel:
                # Suggest alternative channel
                alt_channel = await self._get_alternative_channel(score, rule, channel)
                return {
                    "can_contact": False,
                    "reason": f"Channel '{channel}' weekly limit reached ({channel_count}/{max_channel}).",
                    "recommended_channel": alt_channel,
                    "recommended_wait_hours": 24,
                    "fatigue_level": score.fatigue_level,
                    "contacts_this_week": score.total_contacts_last_7d,
                    "ai_recommendation": f"Canal {channel} saturado. Intentar por {alt_channel}.",
                }

        # Check minimum hours between contacts
        if score.last_contact_at:
            hours_since = (datetime.now(timezone.utc) - score.last_contact_at).total_seconds() / 3600
            if hours_since < rule.min_hours_between_contacts:
                wait_hours = int(rule.min_hours_between_contacts - hours_since)
                return {
                    "can_contact": False,
                    "reason": f"Minimum {rule.min_hours_between_contacts}h between contacts. Wait {wait_hours}h more.",
                    "recommended_channel": None,
                    "recommended_wait_hours": wait_hours,
                    "fatigue_level": score.fatigue_level,
                    "contacts_this_week": score.total_contacts_last_7d,
                    "ai_recommendation": f"Esperar {wait_hours}h más antes de contactar.",
                }

        # Check business hours
        if rule.respect_local_hours:
            now = datetime.now(timezone.utc)
            # Simplified: use UTC for now, in production would use lead's timezone
            current_hour = now.hour
            if not (rule.allowed_hours_start <= current_hour < rule.allowed_hours_end):
                return {
                    "can_contact": False,
                    "reason": f"Outside allowed hours ({rule.allowed_hours_start}:00 - {rule.allowed_hours_end}:00).",
                    "recommended_channel": None,
                    "recommended_wait_hours": rule.allowed_hours_start - current_hour if current_hour < rule.allowed_hours_start else (24 - current_hour + rule.allowed_hours_start),
                    "fatigue_level": score.fatigue_level,
                    "contacts_this_week": score.total_contacts_last_7d,
                    "ai_recommendation": f"Fuera de horario permitido. Contactar entre {rule.allowed_hours_start}:00 y {rule.allowed_hours_end}:00.",
                }

        # Check weekend avoidance
        if rule.avoid_weekends:
            now = datetime.now(timezone.utc)
            if now.weekday() >= 5:  # Saturday=5, Sunday=6
                return {
                    "can_contact": False,
                    "reason": "Weekend contact avoided per business rules.",
                    "recommended_channel": None,
                    "recommended_wait_hours": (7 - now.weekday()) * 24,
                    "fatigue_level": score.fatigue_level,
                    "contacts_this_week": score.total_contacts_last_7d,
                    "ai_recommendation": "Evitar contactar fines de semana. Esperar al lunes.",
                }

        # All checks passed
        recommended_channel = channel or await self._get_best_channel(score, rule)
        return {
            "can_contact": True,
            "reason": "All checks passed. Contact is allowed.",
            "recommended_channel": recommended_channel,
            "recommended_wait_hours": 0,
            "fatigue_level": score.fatigue_level,
            "contacts_this_week": score.total_contacts_last_7d,
            "ai_recommendation": f"Contacto permitido por canal {recommended_channel}.",
        }

    async def record_contact(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        channel: str,
        message_type: str,
        message_content: str | None = None,
        workflow_execution_id: uuid.UUID | None = None,
        ai_generated: bool = False,
    ) -> OutreachLog:
        """Record an outreach attempt and update fatigue score."""
        log = OutreachLog(
            business_id=business_id,
            conversation_id=conversation_id,
            channel=channel,
            message_type=message_type,
            message_content=message_content[:500] if message_content else None,
            workflow_execution_id=workflow_execution_id,
            ai_generated=ai_generated,
        )
        self.db.add(log)

        # Update fatigue score
        score = await self.get_or_create_score(business_id, conversation_id)
        score.last_contact_at = datetime.now(timezone.utc)

        # Recalculate weekly counts
        await self._recalculate_counts(score)

        # Update channel count
        channel_counts = dict(score.contacts_by_channel)
        channel_counts[channel] = channel_counts.get(channel, 0) + 1
        score.contacts_by_channel = channel_counts

        # Determine fatigue level
        score.fatigue_level = self._calculate_fatigue_level(score)

        # Set cooldown if needed
        rule = await self.get_or_create_rule(business_id)
        if score.consecutive_no_replies >= rule.cooldown_after_no_reply_count:
            score.recommended_cooldown_until = datetime.now(timezone.utc) + timedelta(days=rule.long_cooldown_days)
            score.ai_recommendation = f"Lead no responde tras {score.consecutive_no_replies} intentos. Pausar {rule.long_cooldown_days} días."
        else:
            score.recommended_cooldown_until = None
            score.ai_recommendation = None

        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def record_response(
        self,
        conversation_id: uuid.UUID,
        response_type: str = "neutral",
        response_content: str | None = None,
    ) -> None:
        """Record that a lead responded — resets consecutive no-replies."""
        result = await self.db.execute(
            select(ContactFatigueScore).where(ContactFatigueScore.conversation_id == conversation_id)
        )
        score = result.scalar_one_or_none()
        if not score:
            return

        score.last_response_at = datetime.now(timezone.utc)
        score.consecutive_no_replies = 0
        score.recommended_cooldown_until = None
        score.ai_recommendation = None

        # Update the latest outreach log
        log_result = await self.db.execute(
            select(OutreachLog).where(
                OutreachLog.conversation_id == conversation_id,
            ).order_by(desc(OutreachLog.sent_at)).limit(1)
        )
        log = log_result.scalar_one_or_none()
        if log:
            log.status = OutreachLogStatus.RESPONDED
            log.responded_at = datetime.now(timezone.utc)
            log.response_type = response_type
            log.response_content = response_content[:500] if response_content else None

        await self.db.commit()

    async def _recalculate_counts(self, score: ContactFatigueScore) -> None:
        """Recalculate 7d and 30d contact counts from logs."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Count last 7 days
        week_result = await self.db.execute(
            select(func.count(OutreachLog.id)).where(
                OutreachLog.conversation_id == score.conversation_id,
                OutreachLog.sent_at >= week_ago,
            )
        )
        score.total_contacts_last_7d = week_result.scalar() or 0

        # Count last 30 days
        month_result = await self.db.execute(
            select(func.count(OutreachLog.id)).where(
                OutreachLog.conversation_id == score.conversation_id,
                OutreachLog.sent_at >= month_ago,
            )
        )
        score.total_contacts_last_30d = month_result.scalar() or 0

        # Count consecutive no-replies
        logs_result = await self.db.execute(
            select(OutreachLog).where(
                OutreachLog.conversation_id == score.conversation_id,
            ).order_by(desc(OutreachLog.sent_at))
        )
        logs = logs_result.scalars().all()
        consecutive = 0
        for log in logs:
            if log.status == OutreachLogStatus.RESPONDED:
                break
            consecutive += 1
        score.consecutive_no_replies = consecutive

    def _calculate_fatigue_level(self, score: ContactFatigueScore) -> FatigueLevel:
        """Determine fatigue level based on contact frequency."""
        if score.total_contacts_last_7d >= 6 or score.consecutive_no_replies >= 4:
            return FatigueLevel.EXHAUSTED
        elif score.total_contacts_last_7d >= 4 or score.consecutive_no_replies >= 3:
            return FatigueLevel.TIRED
        elif score.total_contacts_last_7d >= 2:
            return FatigueLevel.NORMAL
        return FatigueLevel.RELAXED

    async def _is_hot_lead(self, conversation_id: uuid.UUID) -> bool:
        """Check if a lead is classified as hot."""
        result = await self.db.execute(
            select(LeadScore).where(LeadScore.conversation_id == conversation_id)
        )
        ls = result.scalar_one_or_none()
        return ls is not None and ls.classification == "hot"

    async def _get_best_channel(self, score: ContactFatigueScore, rule: OutreachCadenceRule) -> str | None:
        """Recommend the best channel based on fatigue and priority."""
        for channel in rule.channel_priority:
            channel_count = score.contacts_by_channel.get(channel, 0)
            if channel_count < rule.max_messages_per_channel_per_week:
                return channel
        return rule.channel_priority[0] if rule.channel_priority else None

    async def _get_alternative_channel(self, score: ContactFatigueScore, rule: OutreachCadenceRule, exclude: str) -> str | None:
        """Suggest an alternative channel."""
        for channel in rule.channel_priority:
            if channel == exclude:
                continue
            channel_count = score.contacts_by_channel.get(channel, 0)
            if channel_count < rule.max_messages_per_channel_per_week:
                return channel
        return None

    async def recalculate_all_scores(self, business_id: uuid.UUID) -> int:
        """Recalculate fatigue scores for all conversations of a business."""
        result = await self.db.execute(
            select(ContactFatigueScore).where(ContactFatigueScore.business_id == business_id)
        )
        scores = result.scalars().all()
        for score in scores:
            await self._recalculate_counts(score)
            score.fatigue_level = self._calculate_fatigue_level(score)
        await self.db.commit()
        return len(scores)


class CadenceEngine:
    """Orchestrates smart follow-up sequences respecting fatigue."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    async def get_next_action_for_lead(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Determine the next best action for a lead."""
        # Check fatigue
        contact_check = await self.fatigue.can_contact_now(business_id, conversation_id)

        if not contact_check["can_contact"]:
            return {
                "conversation_id": conversation_id,
                "recommended_action": "wait",
                "recommended_channel": contact_check.get("recommended_channel"),
                "recommended_message_type": None,
                "recommended_delay_hours": contact_check.get("recommended_wait_hours", 24),
                "reason": contact_check["reason"],
                "fatigue_level": contact_check["fatigue_level"],
            }

        # Determine message type based on lead state
        message_type = await self._determine_message_type(business_id, conversation_id)
        channel = contact_check["recommended_channel"]

        return {
            "conversation_id": conversation_id,
            "recommended_action": "send_message",
            "recommended_channel": channel,
            "recommended_message_type": message_type,
            "recommended_delay_hours": 0,
            "reason": f"Contacto permitido. Enviar {message_type} por {channel}.",
            "fatigue_level": contact_check["fatigue_level"],
        }

    async def _determine_message_type(self, business_id: uuid.UUID, conversation_id: uuid.UUID) -> str:
        """Determine what kind of message to send based on conversation state."""
        # Get last outreach
        result = await self.db.execute(
            select(OutreachLog).where(
                OutreachLog.conversation_id == conversation_id,
            ).order_by(desc(OutreachLog.sent_at)).limit(1)
        )
        last_log = result.scalar_one_or_none()

        if not last_log:
            return "welcome"

        # Get conversation and deal state
        from app.domains.crm.models import Deal
        deal_result = await self.db.execute(
            select(Deal).where(
                Deal.conversation_id == conversation_id,
                Deal.is_active == True,
            )
        )
        deal = deal_result.scalar_one_or_none()

        if deal:
            if deal.stage == "proposal_sent":
                return "follow_up_proposal"
            elif deal.stage == "negotiating":
                return "urgency_reminder"
            elif deal.stage == "closed_won":
                return "onboarding"
            elif deal.stage == "closed_lost":
                return "win_back"
            else:
                return "nurture"

        # No deal yet — nurture
        if last_log.message_type in ("welcome", "qualification"):
            return "value_proposition"
        elif last_log.message_type == "value_proposition":
            return "social_proof"
        else:
            return "nurture"

    async def process_workflow_send_message(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        channel: str,
        message_content: str,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Hook for WorkflowEngine: checks fatigue before sending any message."""
        contact_check = await self.fatigue.can_contact_now(business_id, conversation_id, channel)

        if not contact_check["can_contact"]:
            logger.info(
                f"Workflow message blocked by fatigue check for conv {conversation_id}: "
                f"{contact_check['reason']}"
            )
            return {
                "allowed": False,
                "reason": contact_check["reason"],
                "recommended_delay_hours": contact_check.get("recommended_wait_hours"),
            }

        # Record the contact
        await self.fatigue.record_contact(
            business_id=business_id,
            conversation_id=conversation_id,
            channel=channel,
            message_type="workflow",
            message_content=message_content,
            workflow_execution_id=workflow_execution_id,
            ai_generated=False,
        )

        return {"allowed": True, "reason": "Contact allowed by cadence engine."}
