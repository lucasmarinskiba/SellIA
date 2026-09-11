"""What the seller configures about themselves, their market and their taste.

Deliberately NOT a third copy of the business profile. The niche, the audience,
the countries and the goals already live in BusinessContext, and the language,
tone and interests already live in UserMemory; the preferences API reads and
writes those in place. This table holds only what neither of them had: where the
seller wants to sell, in which languages, under which limits, and the things the
AI must never say on their behalf.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class SellerPreferences(Base):
    __tablename__ = "seller_preferences"
    __table_args__ = (UniqueConstraint("business_id", name="uq_seller_preferences_business"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Where the seller wants to sell. Distinct from the channels actually
    # connected: this is intent, and the difference between the two is what the
    # suggestions screen is for.
    target_platforms = Column(JSONB, default=list, nullable=False)      # ["mercadolibre", "instagram"]
    # Languages the business sells in, most important first. The bot answers in
    # the customer's language when it is one of these.
    languages = Column(JSONB, default=list, nullable=False)             # ["es", "pt"]
    # Markets, as ISO country codes, ordered by importance.
    markets = Column(JSONB, default=list, nullable=False)               # ["AR", "UY"]
    # Free-form tastes: what this seller likes selling, the style they want,
    # references they admire. Fed to the prompt composer as context.
    tastes = Column(JSONB, default=list, nullable=False)                # ["diseño minimalista", ...]
    # Words and topics the AI must never use on their behalf.
    banned_topics = Column(JSONB, default=list, nullable=False)
    # The currency the dashboards display by default when a business has more
    # than one. Never used to convert: only to pick which total leads.
    display_currency = Column(String(3), nullable=True)
    # How the seller wants the bot to sound beyond the tone preset.
    voice_notes = Column(Text, nullable=True)
    # Whether the AI may answer customers without a human reading first.
    autonomous_replies = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
