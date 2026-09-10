"""Per-platform chatbot configuration.

Until now a business had exactly one AgentConfig: the AI was either answering
everywhere or nowhere, always with the same hardcoded default personality
("captador"). That is the wrong shape for how people actually sell. A buyer
asking a price on a MercadoLibre listing, a follower sliding into Instagram DMs,
and a customer writing on WhatsApp after buying are three different
conversations, and a seller reasonably wants a different bot -- or no bot -- on
each.

The sales intelligence itself already exists and is already wired: ai_reply.py
detects the funnel stage of a conversation (awareness, acquisition, conversion,
retention, expansion) and layers the matching specialist prompt and expert voice
over the base personality. What was missing was per-platform control over it,
which is what these rows are.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class BotFocus(str, enum.Enum):
    """What this platform's bot is mainly there to do.

    AUTO leaves it to the funnel-stage detector, which reads the actual
    conversation. The rest pin the stage, for sellers who know what a given
    channel is for.
    """

    AUTO = "auto"
    ATTRACT = "acquisition"    # atraer clientes / generar interés
    CLOSE = "conversion"       # cerrar la venta
    RETAIN = "retention"       # fidelizar / posventa
    GROW = "expansion"         # upsell, cross-sell, referidos


class PlatformBot(Base):
    __tablename__ = "platform_bots"
    __table_args__ = (
        UniqueConstraint("business_id", "platform", name="uq_platform_bots_business_platform"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    platform = Column(String(40), nullable=False)

    #: Whether the AI answers on this platform at all.
    enabled = Column(Boolean, nullable=False, default=False)
    #: Base personality slug (agent_personalities.slug). NULL = platform default.
    personality_slug = Column(String(50), nullable=True)
    focus = Column(Enum(BotFocus), nullable=False, default=BotFocus.AUTO)
    #: Extra instructions appended to this bot's prompt, in the seller's words.
    custom_instructions = Column(Text, nullable=True)

    #: Words that hand the conversation to a human instead of answering. Real
    #: behaviour: the conversation is flagged awaiting_human, which the
    #: auto-reply path already refuses to touch.
    handoff_keywords = Column(JSONB, nullable=False, default=list)
    #: Stop after this many AI messages in one conversation without a human
    #: stepping in. NULL = no cap.
    max_ai_replies = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


CHATBOT_TABLES = [PlatformBot.__table__]
