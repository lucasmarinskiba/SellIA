"""Multi-user-per-business membership. Was entirely missing from the app's
data model until this fix: Business.user_id is a single owner column, and
subscriptions/models.py's pricing tiers already reference a "team_members"
limit (1 on free, 2/5/-1 on paid tiers) that nothing enforced because the
underlying membership relationship was never built.

Simple roles per explicit product decision: owner (Business.user_id itself,
not a row here), admin, member. No invitation-email flow yet -- this is the
data model + the direct-add/role/remove endpoints; inviting by email is a
separate feature.
"""
import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, DateTime, Enum, Boolean, Text, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class BusinessMemberRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class BusinessMember(Base):
    """A user granted access to a business beyond its owner.

    The owner (Business.user_id) is NOT represented as a row here -- they
    already have full access via that column. This table is for everyone
    else added to the team.
    """
    __tablename__ = "business_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(BusinessMemberRole), default=BusinessMemberRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_business_member"),
        Index("ix_business_members_business_id", "business_id"),
    )


class DealDelegation(Base):
    """A request to hand off a set of deals from one team member to
    another (e.g. someone going on leave). Replaces the original mock's
    "delegate AgentType" concept -- AgentType (LEAD_SCOUT/CLOSER_BOT/
    COACH_AGENT/ANALYTICS_ENGINE) had no real backing anywhere else in the
    app (no AI-agent-role assignment system exists), so delegating "agent
    types" to a person had nothing real to attach to. Delegating actual
    Deal ownership does.
    """
    __tablename__ = "deal_delegations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    deal_ids = Column(JSONB, default=list, nullable=False)  # [uuid_str, ...] -- the specific deals being handed off
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_deal_delegations_business_id", "business_id"),
        Index("ix_deal_delegations_to_user", "to_user_id", "status"),
    )
