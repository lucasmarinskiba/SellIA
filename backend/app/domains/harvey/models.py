"""Harvey tables — every row is scoped to a business.

Tables
------
harvey_profiles   One row per business: persona, offer, compliance settings.
harvey_prospects  People/companies to contact for a business.
harvey_outbox     Drafted emails; nothing leaves without human approval.
harvey_replies    Replies logged against a prospect, with classification.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProspectStatus(str, enum.Enum):
    NEW = "new"
    DRAFTED = "drafted"
    REPLIED = "replied"
    OPTED_OUT = "opted_out"
    WRITE_FAILED = "write_failed"
    CONTACTED = "contacted"  # at least one email of the sequence went out
    COMPLETED = "completed"  # whole sequence sent, no reply
    BOUNCED = "bounced"


class OutboxStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"  # failed the deterministic gate
    SENDING = "sending"  # claimed by a send in progress; stops double-sends
    SENT = "sent"
    FAILED = "failed"  # SMTP kept failing; needs a person


class ReplyClass(str, enum.Enum):
    INTERESTED = "interested"
    OBJECTION = "objection"
    QUESTION = "question"
    NOT_INTERESTED = "not_interested"
    OPT_OUT = "opt_out"
    HANDOFF = "handoff"  # a human has to answer (contract, legal, price negotiation)


class HarveyProfile(Base):
    __tablename__ = "harvey_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    is_enabled = Column(Boolean, default=False, nullable=False)
    persona_name = Column(String(120), nullable=False, default="")
    persona_role = Column(String(120), nullable=False, default="Desarrollo de negocios")
    tone = Column(String(255), nullable=False, default="profesional, cercano, directo")
    language = Column(String(8), nullable=False, default="es")
    offer = Column(Text, nullable=False, default="")
    benefits = Column(JSONB, nullable=False, default=list)
    icp = Column(JSONB, nullable=False, default=dict)
    postal_address = Column(String(300), nullable=False, default="")
    opt_out_line = Column(
        String(300),
        nullable=False,
        default='¿No te interesa? Respondé "no gracias" y no te escribo más.',
    )
    do_not_contact = Column(JSONB, nullable=False, default=list)
    max_daily_drafts = Column(Integer, nullable=False, default=20)
    max_daily_sends = Column(Integer, nullable=False, default=30)
    # IMAP cursor: highest UID already looked at (0 = never synced).
    imap_last_uid = Column(Integer, nullable=False, default=0)
    inbox_synced_at = Column(DateTime(timezone=True), nullable=True)
    # Automatic loop (Celery beat). Sending happens only inside the window, and a young
    # mailbox ramps up from warmup_started_at instead of blasting max_daily_sends on day 1.
    auto_draft = Column(Boolean, nullable=False, default=False)
    auto_discover = Column(Boolean, nullable=False, default=False)
    max_daily_discoveries = Column(Integer, nullable=False, default=10)
    send_window_start = Column(Integer, nullable=False, default=9)
    send_window_end = Column(Integer, nullable=False, default=18)
    send_timezone = Column(String(64), nullable=False, default="America/Argentina/Buenos_Aires")
    send_weekdays_only = Column(Boolean, nullable=False, default=True)
    warmup_started_at = Column(DateTime(timezone=True), nullable=True)
    last_cycle_at = Column(DateTime(timezone=True), nullable=True)
    last_cycle = Column(JSONB, nullable=False, default=dict)
    last_discovery_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class HarveyProspect(Base):
    __tablename__ = "harvey_prospects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email = Column(String(320), nullable=False)
    first_name = Column(String(120), nullable=False, default="")
    last_name = Column(String(120), nullable=False, default="")
    title = Column(String(160), nullable=False, default="")
    company = Column(String(255), nullable=False, default="")
    industry = Column(String(160), nullable=False, default="")
    website = Column(String(500), nullable=False, default="")
    # [{"type": "hiring", "detail": "busca un community manager"}] — facts the
    # writer may cite. Anything not here is not allowed in an email.
    signals = Column(JSONB, nullable=False, default=list)
    notes = Column(Text, nullable=False, default="")
    # "provided": supplied by the business (own CRM/list). "invalid"/"guess" never get mail.
    email_status = Column(String(20), nullable=False, default="provided")
    is_company_inbox = Column(Boolean, nullable=False, default=False)
    # Where the prospect came from: "manual" (the business's own list) or "discovery"
    # (an address published on the prospect's own site, found by us; needs a human to verify).
    source = Column(String(20), nullable=False, default="manual")
    source_url = Column(String(500), nullable=False, default="")
    status = Column(String(20), nullable=False, default=ProspectStatus.NEW.value, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("business_id", "email", name="uq_harvey_prospect_business_email"),)

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class HarveyOutboxItem(Base):
    __tablename__ = "harvey_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prospect_id = Column(
        UUID(as_uuid=True), ForeignKey("harvey_prospects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 1-3 = the cold sequence. Answers to a prospect's reply use REPLY_STEP_BASE + n so the
    # (business, prospect, step) slot stays unique; they are told apart by kind.
    step = Column(Integer, nullable=False, default=1)
    kind = Column(String(10), nullable=False, default="sequence")
    reply_id = Column(UUID(as_uuid=True), nullable=True)
    to_email = Column(String(320), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default=OutboxStatus.PENDING_REVIEW.value, index=True)
    gate_reasons = Column(JSONB, nullable=False, default=list)
    decided_by = Column(UUID(as_uuid=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    # RFC 5322 Message-ID of what we sent, and of the email it follows up on:
    # replies are matched to a prospect through these, and follow-ups thread.
    message_id = Column(String(255), nullable=True, index=True)
    in_reply_to = Column(String(255), nullable=True)
    send_attempts = Column(Integer, nullable=False, default=0)
    send_error = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("business_id", "prospect_id", "step", name="uq_harvey_outbox_slot"),
        Index("ix_harvey_outbox_business_status", "business_id", "status"),
    )


class HarveyReply(Base):
    __tablename__ = "harvey_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prospect_id = Column(
        UUID(as_uuid=True), ForeignKey("harvey_prospects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body = Column(Text, nullable=False)
    # Message-ID of an email read from the inbox; makes syncing idempotent.
    message_id = Column(String(255), nullable=True)
    classification = Column(String(20), nullable=False)
    needs_human = Column(Boolean, nullable=False, default=False)
    draft_answer = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("business_id", "message_id", name="uq_harvey_reply_message"),)
