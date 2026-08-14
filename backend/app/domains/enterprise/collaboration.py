"""Phase 26: Team Collaboration Hub - Real-time deal collaboration, approvals, handoffs."""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import enum

from backend.app.database import Base


class CollaborationActionEnum(str, enum.Enum):
    """Actions that require approval."""
    DISCOUNT = "discount"
    ESCALATION = "escalation"
    HANDOFF = "handoff"
    PROPOSAL = "proposal"
    CLOSE = "close"


class ApprovalStatusEnum(str, enum.Enum):
    """Approval workflow states."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DealComment(Base):
    """Comments on deals (team collaboration)."""
    __tablename__ = "deal_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    mentions = Column(String(500), nullable=True)  # CSV: @user_id, @user_id
    is_internal = Column(Boolean, default=True)  # Don't send to buyer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_deal_comments', 'deal_id', 'created_at'),
    )


class ApprovalChain(Base):
    """Multi-step approvals (e.g., manager sign-off on discounts)."""
    __tablename__ = "approval_chains"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id = Column(String(255), nullable=False)  # discount-12345, escalation-67890
    action_type = Column(String(50), nullable=False)  # DISCOUNT, ESCALATION, etc
    requester_id = Column(String(255), nullable=False)
    requester_name = Column(String(255), nullable=False)

    # Chain steps (JSON format: [{"approver_id": "...", "status": "pending"}])
    approval_steps = Column(Text, nullable=False)  # Serialized JSON

    status = Column(String(20), default="pending")  # pending, approved, rejected
    decision_by = Column(String(255), nullable=True)
    decision_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_approval_action', 'action_id'),
        Index('idx_approval_status', 'status', 'created_at'),
    )


class Handoff(Base):
    """Deal handoff between team members (with notes)."""
    __tablename__ = "handoffs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = Column(String(255), nullable=False)
    from_user_id = Column(String(255), nullable=False)
    from_user_name = Column(String(255), nullable=False)
    to_user_id = Column(String(255), nullable=False)
    to_user_name = Column(String(255), nullable=False)

    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # Deal state snapshot

    status = Column(String(20), default="pending")  # pending, accepted, rejected
    accepted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_handoff_deal', 'deal_id', 'created_at'),
        Index('idx_handoff_user', 'to_user_id', 'status'),
    )


class TeamNotification(Base):
    """Real-time notifications (comments, approvals, handoffs)."""
    __tablename__ = "team_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # comment, approval_requested, handoff, etc
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    related_deal_id = Column(String(255), nullable=True)
    related_user_id = Column(String(255), nullable=True)  # Who triggered it

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_notif_user', 'user_id', 'is_read', 'created_at'),
    )


# ── Collaboration Manager ──
class CollaborationManager:
    """Business logic for team collaboration."""

    @staticmethod
    async def add_comment(
        db: AsyncSession,
        deal_id: str,
        user_id: str,
        user_name: str,
        content: str,
        mentions: list[str] | None = None,
    ) -> DealComment:
        """Add comment to deal. Broadcasts to team via WebSocket."""
        comment = DealComment(
            deal_id=deal_id,
            user_id=user_id,
            user_name=user_name,
            content=content,
            mentions=",".join(mentions) if mentions else None,
            is_internal=True,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        # Broadcast to all users viewing this deal
        # WebSocket message: {"type": "comment.added", "deal_id": deal_id, "comment": {...}}

        return comment

    @staticmethod
    async def request_approval(
        db: AsyncSession,
        action_id: str,
        action_type: CollaborationActionEnum,
        requester_id: str,
        requester_name: str,
        approver_ids: list[str],
    ) -> ApprovalChain:
        """Request approval for action (discount, escalation, etc)."""
        import json

        approval_steps = json.dumps(
            [{"approver_id": aid, "status": "pending"} for aid in approver_ids]
        )

        chain = ApprovalChain(
            action_id=action_id,
            action_type=action_type.value,
            requester_id=requester_id,
            requester_name=requester_name,
            approval_steps=approval_steps,
            status="pending",
        )
        db.add(chain)
        await db.commit()
        await db.refresh(chain)
        return chain

    @staticmethod
    async def approve_action(
        db: AsyncSession,
        action_id: str,
        approver_id: str,
        decision: str,  # "approved" or "rejected"
        rejection_reason: str | None = None,
    ) -> ApprovalChain:
        """Process approval decision."""
        import json

        stmt = select(ApprovalChain).where(ApprovalChain.action_id == action_id)
        result = await db.execute(stmt)
        chain = result.scalars().first()

        if not chain:
            raise ValueError(f"Action {action_id} not found")

        # Update step status
        steps = json.loads(chain.approval_steps)
        for step in steps:
            if step["approver_id"] == approver_id:
                step["status"] = decision

        chain.approval_steps = json.dumps(steps)

        # Check if all approved
        all_approved = all(step["status"] == "approved" for step in steps)
        if all_approved:
            chain.status = "approved"
            chain.decision_by = approver_id
            chain.decision_at = datetime.utcnow()
        elif decision == "rejected":
            chain.status = "rejected"
            chain.decision_by = approver_id
            chain.decision_at = datetime.utcnow()
            chain.rejection_reason = rejection_reason

        await db.commit()
        await db.refresh(chain)
        return chain

    @staticmethod
    async def create_handoff(
        db: AsyncSession,
        deal_id: str,
        from_user_id: str,
        from_user_name: str,
        to_user_id: str,
        to_user_name: str,
        reason: str,
        notes: str,
    ) -> Handoff:
        """Create deal handoff (pass to teammate)."""
        handoff = Handoff(
            deal_id=deal_id,
            from_user_id=from_user_id,
            from_user_name=from_user_name,
            to_user_id=to_user_id,
            to_user_name=to_user_name,
            reason=reason,
            notes=notes,
        )
        db.add(handoff)
        await db.commit()
        await db.refresh(handoff)
        return handoff
