"""Revenue Attribution Engine

Traces back through a conversation to attribute revenue to:
- First touch channel
- Last touch channel
- Last workflow executed
- Last agent that responded
- All intermediate touchpoints
"""

import uuid
from typing import Optional, Dict, Any, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.channels.models import Conversation, Message
from app.domains.automations.models import WorkflowExecution
from app.domains.agents.models import AgentConversation, AgentMessage
from app.domains.orders.models import Order


class RevenueAttributionEngine:
    """Engine that attributes revenue to channels, workflows, and agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def attrib_order(self, order: Order) -> Dict[str, Any]:
        """Populate attribution fields on an order before saving."""
        if not order.conversation_id:
            order.attribution_model = "last_touch"
            order.source_channel = "manual"
            return {"model": "manual", "reason": "no_conversation"}

        # Get conversation
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == order.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            order.attribution_model = "last_touch"
            order.source_channel = "manual"
            return {"model": "manual", "reason": "conversation_not_found"}

        # Get all messages in conversation
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        # Get workflow executions for this conversation
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.conversation_id == conversation.id
            ).order_by(desc(WorkflowExecution.executed_at))
        )
        executions = result.scalars().all()

        # Get agent conversations for this business
        result = await self.db.execute(
            select(AgentConversation).where(
                AgentConversation.business_id == conversation.business_id
            )
        )
        agent_convs = result.scalars().all()
        agent_conv_ids = [ac.id for ac in agent_convs]

        last_agent_message = None
        if agent_conv_ids:
            result = await self.db.execute(
                select(AgentMessage).where(
                    AgentMessage.agent_conversation_id.in_(agent_conv_ids)
                ).order_by(desc(AgentMessage.created_at)).limit(1)
            )
            last_agent_message = result.scalar_one_or_none()

        # Determine attribution
        touchpoints = []

        # First touch
        first_message = messages[0] if messages else None
        first_touch_channel = conversation.platform.value if conversation.platform else "unknown"
        order.first_touch_channel = first_touch_channel
        touchpoints.append({
            "type": "first_touch",
            "channel": first_touch_channel,
            "timestamp": first_message.created_at.isoformat() if first_message else None,
        })

        # Last touch
        last_inbound = None
        for m in reversed(messages):
            if m.direction.value == "inbound":
                last_inbound = m
                break
        last_touch_channel = conversation.platform.value if conversation.platform else "unknown"
        order.last_touch_channel = last_touch_channel
        touchpoints.append({
            "type": "last_touch",
            "channel": last_touch_channel,
            "timestamp": last_inbound.created_at.isoformat() if last_inbound else None,
        })

        # Workflow attribution (last executed)
        if executions:
            last_execution = executions[0]
            order.source_workflow_id = last_execution.workflow_id
            touchpoints.append({
                "type": "workflow",
                "workflow_id": str(last_execution.workflow_id),
                "timestamp": last_execution.executed_at.isoformat() if last_execution.executed_at else None,
            })

        # Agent attribution (last agent that responded)
        if last_agent_message:
            order.source_agent_id = last_agent_message.personality_id
            touchpoints.append({
                "type": "agent",
                "agent_id": str(last_agent_message.personality_id) if last_agent_message.personality_id else None,
                "timestamp": last_agent_message.created_at.isoformat() if last_agent_message.created_at else None,
            })

        # Set primary source channel
        order.source_channel = last_touch_channel
        order.attribution_model = "last_touch"

        return {
            "model": "last_touch",
            "touchpoints": touchpoints,
            "conversation_id": str(conversation.id),
        }

    async def get_conversation_touchpoints(
        self,
        conversation_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Get all touchpoints for a conversation."""
        touchpoints = []

        # Messages
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        for m in messages:
            touchpoints.append({
                "type": "message",
                "direction": m.direction.value,
                "timestamp": m.created_at.isoformat() if m.created_at else None,
            })

        # Workflow executions
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.conversation_id == conversation_id
            ).order_by(WorkflowExecution.executed_at)
        )
        executions = result.scalars().all()

        for e in executions:
            touchpoints.append({
                "type": "workflow_execution",
                "workflow_id": str(e.workflow_id),
                "status": e.status,
                "timestamp": e.executed_at.isoformat() if e.executed_at else None,
            })

        # Sort by timestamp
        touchpoints.sort(key=lambda x: x.get("timestamp") or "")

        return touchpoints
