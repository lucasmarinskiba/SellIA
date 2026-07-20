"""Proactive Outreach Engine Service

CRUD and execution layer for outreach opportunities and rules.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.proactive.models import OutreachOpportunity, OutreachRule
from app.domains.proactive.engine import ProactiveEngine
from app.domains.memory.models import ConversationMemoryChunk
from app.domains.channels.models import Conversation, Message, MessageDirection, MessageStatus
from app.domains.channels.services import send_outbound_message

logger = get_logger(__name__)


class ProactiveService:
    """Service layer for proactive outreach operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = ProactiveEngine(db)

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    async def create_rule(
        self,
        business_id: uuid.UUID,
        rule_data: Dict[str, Any],
    ) -> OutreachRule:
        """Create a new outreach rule for a business."""
        rule = OutreachRule(
            business_id=business_id,
            rule_name=rule_data["rule_name"],
            rule_type=rule_data["rule_type"],
            conditions=rule_data.get("conditions", {}),
            message_template=rule_data["message_template"],
            channel=rule_data.get("channel", "whatsapp"),
            is_active=rule_data.get("is_active", True),
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_rules(
        self,
        business_id: uuid.UUID,
        active_only: bool = True,
    ) -> List[OutreachRule]:
        """List outreach rules for a business."""
        stmt = select(OutreachRule).where(OutreachRule.business_id == business_id)
        if active_only:
            stmt = stmt.where(OutreachRule.is_active == True)
        stmt = stmt.order_by(desc(OutreachRule.updated_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_rule(self, rule_id: uuid.UUID) -> Optional[OutreachRule]:
        """Get a single rule by ID."""
        result = await self.db.execute(
            select(OutreachRule).where(OutreachRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[OutreachRule]:
        """Update an outreach rule."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return None

        for field, value in update_data.items():
            if hasattr(rule, field) and value is not None:
                setattr(rule, field, value)

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    # ------------------------------------------------------------------
    # Opportunities
    # ------------------------------------------------------------------

    async def list_opportunities(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[OutreachOpportunity]:
        """List outreach opportunities with optional filters."""
        stmt = select(OutreachOpportunity).where(
            OutreachOpportunity.business_id == business_id
        )
        if status:
            stmt = stmt.where(OutreachOpportunity.status == status)
        if priority:
            stmt = stmt.where(OutreachOpportunity.priority == priority)
        stmt = stmt.order_by(desc(OutreachOpportunity.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_opportunity(
        self,
        opportunity_id: uuid.UUID,
    ) -> Optional[OutreachOpportunity]:
        """Get a single opportunity by ID."""
        result = await self.db.execute(
            select(OutreachOpportunity).where(OutreachOpportunity.id == opportunity_id)
        )
        return result.scalar_one_or_none()

    async def execute_outreach(
        self,
        opportunity_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Execute outreach for an opportunity: generate message and send via channel."""
        opp = await self.get_opportunity(opportunity_id)
        if not opp:
            return {"status": "error", "detail": "Opportunity not found"}

        if opp.status not in ("pending", "scheduled"):
            return {"status": "error", "detail": f"Opportunity already {opp.status}"}

        # Generate message if not already present
        message = opp.suggested_message
        if not message:
            message = await self.engine.generate_outreach_message(opp)
            if message:
                opp.suggested_message = message
                await self.db.commit()

        if not message:
            return {"status": "error", "detail": "Could not generate message"}

        # Find conversation for this customer
        conversation_id = await self._find_conversation_for_customer(
            opp.business_id, opp.customer_id
        )
        if not conversation_id:
            return {"status": "error", "detail": "No conversation found for customer"}

        # Send via appropriate channel
        try:
            await send_outbound_message(
                self.db,
                conversation_id,
                message,
                "text",
            )
        except Exception as e:
            logger.exception(f"Failed to send outreach for opportunity {opportunity_id}: {e}")
            return {"status": "error", "detail": str(e)}

        opp.status = "sent"
        opp.sent_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "status": "sent",
            "opportunity_id": str(opportunity_id),
            "conversation_id": str(conversation_id),
            "channel": opp.suggested_channel,
        }

    async def dismiss_opportunity(
        self,
        opportunity_id: uuid.UUID,
    ) -> Optional[OutreachOpportunity]:
        """Dismiss an opportunity so it won't be acted upon."""
        opp = await self.get_opportunity(opportunity_id)
        if not opp:
            return None

        opp.status = "dismissed"
        opp.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(opp)
        return opp

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _find_conversation_for_customer(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Find the most recent active conversation for a customer."""
        # Try via conversation memory chunks
        result = await self.db.execute(
            select(ConversationMemoryChunk.conversation_id)
            .where(
                ConversationMemoryChunk.user_id == customer_id,
                ConversationMemoryChunk.business_id == business_id,
            )
            .order_by(desc(ConversationMemoryChunk.created_at))
            .limit(1)
        )
        conv_id = result.scalar_one_or_none()
        if conv_id:
            return conv_id

        # Fallback: any active conversation for the business (less precise)
        result = await self.db.execute(
            select(Conversation.id)
            .where(
                Conversation.business_id == business_id,
                Conversation.is_active == True,
            )
            .order_by(desc(Conversation.last_message_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
