"""Phase 26: Team Collaboration Hub - Real-time deal collaboration, approvals, handoffs."""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import enum

# Was `from app.database import Base` -- an isolated Base with no create-
# table mechanism of its own at all. Switched to the real CoreBase (used by
# Deal/Business, which these tables FK toward conceptually via deal_id/
# user_id) for consistency, though note CoreBase's OWN domain-table auto-
# creation is deliberately skipped app-wide (see app/db/database.py's
# init_db -- "CoreBase domain tables have messy FK relationships (100+
# models)... provisioned via Alembic migrations (currently disabled)").
# These 5 tables are new (this module's read methods didn't exist until
# this fix), so a dedicated CREATE TABLE IF NOT EXISTS bootstrap was added
# to app/sellbot.py's lifespan, matching the same pattern already used
# there for computer_use_audit_logs.
from app.core.database import Base


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


class DealShare(Base):
    """Deal shared with a team member (view/edit access grant).

    Added while completing this module -- api/v1/enterprise_collaboration.py's
    POST /collaboration/share route already existed and called a share_deal()
    method that was never implemented, so this table/model never existed
    either. Minimal schema matching what that route's request/response
    already specified (deal_id, shared_by, shared_with, permissions).
    """
    __tablename__ = "deal_shares"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = Column(String(255), nullable=False)
    shared_by_user_id = Column(String(255), nullable=False)
    shared_with_user_id = Column(String(255), nullable=False)
    permissions = Column(String(20), default="read")  # read, edit
    shared_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_deal_shares_deal', 'deal_id', 'shared_at'),
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
    async def get_deal_comments(db: AsyncSession, deal_id: str, limit: int = 50) -> list[DealComment]:
        """List comments on a deal, most recent first.

        This method (and get_pending_approvals/get_deal_activity_feed/
        share_deal below) didn't exist at all -- api/v1/enterprise_
        collaboration.py's get_comments route called
        collab_manager.get_deal_comments(...), a name that had never been
        implemented, so every call would have raised AttributeError.
        """
        result = await db.execute(
            select(DealComment).where(DealComment.deal_id == deal_id)
            .order_by(DealComment.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def share_deal(
        db: AsyncSession,
        deal_id: str,
        shared_by_user_id: str,
        shared_with_user_id: str,
        permissions: str = "read",
    ) -> DealShare:
        """Share a deal with a teammate (view/edit access grant)."""
        share = DealShare(
            deal_id=deal_id,
            shared_by_user_id=shared_by_user_id,
            shared_with_user_id=shared_with_user_id,
            permissions=permissions,
        )
        db.add(share)
        await db.commit()
        await db.refresh(share)
        return share

    @staticmethod
    async def get_pending_approvals(db: AsyncSession, user_id: str) -> list[ApprovalChain]:
        """List approval chains where `user_id` is an approver still pending
        a decision. approval_steps is stored as a serialized JSON string
        (see approve_action below), not a queryable JSONB column, so this
        fetches pending chains and filters in Python -- matches the same
        JSON handling approve_action already uses for consistency.
        """
        import json

        result = await db.execute(select(ApprovalChain).where(ApprovalChain.status == "pending"))
        chains = result.scalars().all()
        pending = []
        for chain in chains:
            steps = json.loads(chain.approval_steps)
            if any(s["approver_id"] == user_id and s["status"] == "pending" for s in steps):
                pending.append(chain)
        return pending

    @staticmethod
    async def get_deal_activity_feed(db: AsyncSession, deal_id: str, limit: int = 50) -> list[dict]:
        """Combined, timestamp-sorted feed of comments + shares for a deal."""
        comments_result = await db.execute(
            select(DealComment).where(DealComment.deal_id == deal_id)
            .order_by(DealComment.created_at.desc()).limit(limit)
        )
        shares_result = await db.execute(
            select(DealShare).where(DealShare.deal_id == deal_id)
            .order_by(DealShare.shared_at.desc()).limit(limit)
        )

        activity = [
            {
                "type": "comment",
                "id": c.id,
                "user_id": c.user_id,
                "timestamp": c.created_at,
                "content": c.content,
                "mentions": c.mentions.split(",") if c.mentions else [],
            }
            for c in comments_result.scalars().all()
        ] + [
            {
                "type": "share",
                "id": s.id,
                "user_id": s.shared_by_user_id,
                "timestamp": s.shared_at,
                "shared_with": s.shared_with_user_id,
            }
            for s in shares_result.scalars().all()
        ]

        activity.sort(key=lambda a: a["timestamp"], reverse=True)
        return activity[:limit]

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
        """Process approval decision.

        Raises ValueError if action_id doesn't exist OR if approver_id isn't
        actually one of the chain's listed approvers -- previously the loop
        below silently did nothing when approver_id wasn't found, but the
        `elif decision == "rejected"` branch after it fired regardless,
        meaning ANY caller could reject ANY approval chain just by knowing
        its action_id, without ever being a real approver on it.
        """
        import json

        stmt = select(ApprovalChain).where(ApprovalChain.action_id == action_id)
        result = await db.execute(stmt)
        chain = result.scalars().first()

        if not chain:
            raise ValueError(f"Action {action_id} not found")

        # Update step status
        steps = json.loads(chain.approval_steps)
        matched = False
        for step in steps:
            if step["approver_id"] == approver_id:
                step["status"] = decision
                matched = True

        if not matched:
            raise ValueError(f"{approver_id} is not an approver on action {action_id}")

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
