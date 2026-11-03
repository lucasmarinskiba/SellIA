"""Tables of the SellIA -> feedIA sales feed.

``feedia_links``  which feedIA account a business is connected to (set by the business owner).
``feedia_outbox`` one row per sale/refund still to be delivered. A row is written in the SAME transaction as the
order change (see capture.py), so a sale is never lost and never queued twice: (business, event, order) is unique.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FeediaLink(Base):
    __tablename__ = "feedia_links"

    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)
    feedia_account_id = Column(String(64), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class FeediaOutbox(Base):
    __tablename__ = "feedia_outbox"
    __table_args__ = (
        UniqueConstraint("business_id", "event_type", "order_id", name="uq_feedia_outbox_event"),
        Index("ix_feedia_outbox_due", "status", "next_attempt_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(16), nullable=False)  # sale | refund
    order_id = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)  # only strings and ints: see signing.py
    status = Column(String(12), nullable=False, default="pending")  # pending | sent | failed | skipped
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
