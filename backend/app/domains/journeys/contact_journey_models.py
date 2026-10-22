"""Contact journeys: the path of one lead (identified by email or phone) from first contact to repeat purchase.

Deliberately separate from two existing models that look similar:
* ``journeys`` (journey_models.CustomerJourney) is a journey *builder* (a graph of nodes and edges);
* ``customer_journeys`` (attribution_models.CustomerJourney) attributes revenue to registered *users*.

A contact journey has one stage date per funnel stage. Touchpoints are the raw events; the stage dates are
set by the first touchpoint of each stage (see contact_journey_service.STAGE_BY_TOUCHPOINT).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ContactJourney(Base):
    __tablename__ = "contact_journeys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    channel = Column(String(50), nullable=False, index=True)  # organic_search, paid_search, email, proximity_invite...
    campaign = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(20), nullable=True, index=True)

    awareness_date = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
    consideration_date = Column(DateTime(timezone=True), nullable=True)
    intent_date = Column(DateTime(timezone=True), nullable=True)
    visit_date = Column(DateTime(timezone=True), nullable=True)
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    repeat_purchase_count = Column(Integer, nullable=False, default=0)
    last_order_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (Index("ix_contact_journeys_business_awareness", "business_id", "awareness_date"),)


class ContactJourneyTouchpoint(Base):
    __tablename__ = "contact_journey_touchpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("contact_journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    touchpoint_type = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    campaign = Column(String(255), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    order_id = Column(String(255), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
