"""Auto-Close Engine

Detects buying signals and closes deals automatically when conditions are met.
"""

import uuid
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal, LeadStage
from app.domains.channels.models import Conversation, Message
from app.domains.orders.models import Order
from app.domains.autopilot.service import AutopilotEngine, AutopilotActionLog, AutopilotActionType, AutopilotActionStatus
from app.core.logger import get_logger

logger = get_logger(__name__)

# Spanish buying signals (keywords that indicate purchase intent)
BUYING_SIGNALS = [
    r"\bs[ií]\b", r"\bquiero\b", r"\bcompro\b", r"\bpago\b",
    r"\benv[ií]ame\b", r"\bpasame\b", r"\bpásame\b",
    r"\bme interesa\b", r"\blo tomo\b", r"\bagenda\b",
    r"\bhacelo\b", r"\bhagamos\b", r"\bconfirmo\b",
    r"\bperfecto\b", r"\bdale\b", r"\bva\b",
    r"\bmándame\b", r"\bmandame\b",
    r"\bcomprar\b", r"\badquirir\b",
    r"\borden\b", r"\bpedido\b",
    r"\blink de pago\b", r"\bdatos para transferir\b",
    r"\bcuento\b", r"\bhacemos\b",
]

# Signals that indicate doubt (don't auto-close)
DOUBT_SIGNALS = [
    r"\bpensarlo\b", r"\bconsultar\b", r"\bdudas?\b",
    r"\bcaro\b", r"\bcarísimo\b", r"\bmejorar\b",
    r"\bdescuento\b", r"\bpromoción\b", r"\boferta\b",
    r"\bmás barato\b", r"\bcompetencia\b",
    r"\bno s[eé]\b", r"\btodav[ií]a no\b",
]


class AutoCloseEvaluator:
    """Evaluates deals for auto-close signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_all_open_deals(self) -> list[dict[str, Any]]:
        """Evaluate all open deals for auto-close. Returns list of actions taken."""
        from app.domains.autopilot.models import AutopilotConfig

        result = await self.db.execute(
            select(Deal).where(
                Deal.is_active == True,
                Deal.stage.notin_(["closed_won", "closed_lost"]),
            )
        )
        deals = result.scalars().all()

        actions = []
        for deal in deals:
            try:
                action = await self.evaluate_deal(deal)
                if action:
                    actions.append(action)
            except Exception as e:
                logger.exception(f"Auto-close evaluation failed for deal {deal.id}: {e}")

        return actions

    async def evaluate_deal(self, deal: Deal) -> Optional[dict[str, Any]]:
        """Evaluate a single deal for auto-close."""
        from app.domains.autopilot.models import AutopilotConfig

        # Check if autopilot allows auto-close for this business
        config_result = await self.db.execute(
            select(AutopilotConfig).where(AutopilotConfig.business_id == deal.business_id)
        )
        config = config_result.scalar_one_or_none()
        if not config or not config.is_active or config.is_paused or not config.auto_close_deals:
            return None

        # Check amount threshold
        if deal.value and deal.value > config.approval_threshold_amount:
            return None

        # No conversation = no auto-close
        if not deal.conversation_id:
            return None

        # Get recent messages
        messages_result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == deal.conversation_id,
            ).order_by(Message.created_at.desc()).limit(10)
        )
        messages = messages_result.scalars().all()

        if not messages:
            return None

        # Analyze buying signals
        buying_score = 0
        doubt_score = 0
        latest_inbound = None

        for msg in messages:
            if msg.direction == "inbound":
                if not latest_inbound:
                    latest_inbound = msg
                content_lower = msg.content.lower()

                for pattern in BUYING_SIGNALS:
                    if re.search(pattern, content_lower):
                        buying_score += 1

                for pattern in DOUBT_SIGNALS:
                    if re.search(pattern, content_lower):
                        doubt_score += 1

        # Decision logic
        if buying_score >= 2 and doubt_score == 0 and latest_inbound:
            # Strong buying signal, no doubt
            if deal.stage in ["negotiating", "proposal_sent", "qualified"]:
                return await self._auto_close_deal(deal, latest_inbound, config)

        # Check if order already exists for this deal (payment received)
        order_result = await self.db.execute(
            select(Order).where(
                Order.deal_id == deal.id,
                Order.payment_status == "completed",
            )
        )
        existing_order = order_result.scalar_one_or_none()
        if existing_order:
            # Payment received but deal not closed — auto-close
            return await self._auto_close_deal(deal, None, config, reason="Payment received")

        return None

    async def _auto_close_deal(
        self,
        deal: Deal,
        trigger_message: Message | None,
        config,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Auto-close a deal."""
        autopilot = AutopilotEngine(self.db)

        # Move to closed_won
        old_stage = deal.stage
        deal.stage = "closed_won"
        deal.actual_close_date = datetime.now(timezone.utc)
        deal.probability = 100
        deal.close_reason = reason or f"Auto-closed: buying signal detected in conversation"
        deal.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        # Log the action
        await autopilot.log_action(
            business_id=deal.business_id,
            action_type=AutopilotActionType.CLOSE_DEAL,
            entity_type="deal",
            entity_id=deal.id,
            reason=deal.close_reason,
            status=AutopilotActionStatus.EXECUTED,
            context_data={
                "old_stage": old_stage,
                "new_stage": "closed_won",
                "trigger_message_id": str(trigger_message.id) if trigger_message else None,
                "deal_value": float(deal.value) if deal.value else 0,
            },
            revenue_impact=deal.value,
        )

        # Send thank you message
        from app.domains.agents.ai_reply import generate_ai_response
        if deal.conversation_id:
            try:
                await generate_ai_response(
                    db=self.db,
                    business_id=deal.business_id,
                    conversation_id=deal.conversation_id,
                    message_text="confirmacion_compra",
                    personality_slug="post-venta",
                )
            except Exception as e:
                logger.warning(f"Failed to send thank you message for deal {deal.id}: {e}")

        logger.info(f"Auto-closed deal {deal.id} for business {deal.business_id}")

        return {
            "deal_id": str(deal.id),
            "action": "auto_closed",
            "stage_from": old_stage,
            "stage_to": "closed_won",
            "reason": deal.close_reason,
            "revenue": float(deal.value) if deal.value else 0,
        }


class AutoCloseConfigService:
    """Manages auto-close configuration per business."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pending_auto_close_deals(self, business_id: uuid.UUID) -> list[Deal]:
        """Get deals that are candidates for auto-close."""
        result = await self.db.execute(
            select(Deal).where(
                Deal.business_id == business_id,
                Deal.is_active == True,
                Deal.stage.in_(["negotiating", "proposal_sent"]),
            )
        )
        deals = result.scalars().all()

        evaluator = AutoCloseEvaluator(self.db)
        candidates = []
        for deal in deals:
            action = await evaluator.evaluate_deal(deal)
            if action:
                candidates.append(deal)

        return candidates
