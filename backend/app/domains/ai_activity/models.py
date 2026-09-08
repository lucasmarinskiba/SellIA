"""AI Activity Log — durable, per-user record of what SellIA's AI actually did.

Before this, "actividad de la IA" only lived in app.core.brain.activity's
BrainActivityBus: a process-local, in-memory ring buffer (max 300 events,
wiped on every restart/redeploy) with NO user/business scoping at all --
every tenant's Brain dispatch events landed in the same global buffer. That
is fine for the Brain UI's live "synapse firing" animation (which only ever
wants "what just happened, right now, in this process"), but it cannot
answer "what has SellIA's AI done for user X" -- which is exactly what
users see reflected on https://sellia-brain.vercel.app/sellia-brain over
time, across restarts, and without leaking between tenants.

AIActionLog is the durable, per-user/per-business complement: every real
action (a Brain plan dispatched, a workflow executed, a sequence email
sent, etc.) gets one row here, in addition to (not instead of) the existing
in-memory bus which stays exactly as-is for its own purpose.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIActionLog(Base):
    """One real AI/automation action taken on behalf of a SellIA user."""
    __tablename__ = "ai_action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Always attributed to a real, authenticated SellIA account -- rows are
    # never written for anonymous/unscoped callers (see ai_activity/service.py:
    # log_ai_action() is a silent no-op without a user_id).
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Nullable: some actions happen before a user has created any business yet.
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    # What performed the action -- actor_id matches a node id from the Brain
    # registry (app/core/brain/registry.py) when applicable, e.g.
    # "agent.expert.market_analyst" or "automation.check_abandoned_carts",
    # so the frontend can cross-reference back to the 337-node graph.
    actor_type = Column(String(30), nullable=False)   # agent | automation | skill | workflow | brain | system
    actor_id = Column(String(160), nullable=True)

    action = Column(String(80), nullable=False)        # short verb-based type, e.g. "workflow_executed"
    summary = Column(Text, nullable=False)              # human-readable one-liner
    payload = Column(JSONB, default=dict, nullable=False)  # structured details, e.g. {"execution_id": "..."}
    status = Column(String(20), default="success", nullable=False)  # success | failed | skipped

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_ai_action_logs_user_created", "user_id", "created_at"),
        Index("ix_ai_action_logs_business_created", "business_id", "created_at"),
    )


AI_ACTIVITY_TABLES = [AIActionLog.__table__]
