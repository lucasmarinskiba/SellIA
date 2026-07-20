"""Negotiation Engine Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class NegotiationState(Base):
    __tablename__ = "negotiation_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    original_price = Column(Numeric(12, 2), nullable=False)
    current_offer = Column(Numeric(12, 2), nullable=False)
    minimum_acceptable = Column(Numeric(12, 2), nullable=False)
    max_discount_percent = Column(Numeric(5, 2), nullable=False, default=0.0)
    round = Column(Integer, nullable=False, default=0)
    concessions_made = Column(JSONB, default=list)
    status = Column(String(20), nullable=False, default="active")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
