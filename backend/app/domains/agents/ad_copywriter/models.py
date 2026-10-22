import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # meta/google/tiktok
    objective = Column(String(100), nullable=False)
    target_audience = Column(JSONB, default=dict, nullable=False)
    budget = Column(Numeric(12, 2), nullable=True)
    status = Column(String(50), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AdVariant(Base):
    __tablename__ = "ad_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ad_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_name = Column(String(255), nullable=False)
    headline = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    cta = Column(String(100), nullable=False)
    image_prompt = Column(Text, nullable=True)
    targeting = Column(JSONB, default=dict, nullable=False)
    predicted_ctr = Column(Numeric(5, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
