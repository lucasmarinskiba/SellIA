"""Ad-budget autopilot models.

Tables
------
ad_budget_configs        One row per business — autopilot switches + guardrails.
ad_channels              A managed spend channel (meta / google / tiktok / other).
ad_performance_snapshots Rolling-window spend/revenue/ROAS captured each cycle.
budget_reallocations     Decision log: what the optimizer proposed / applied.
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdPlatform(str, enum.Enum):
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    OTHER = "other"


# platform -> ledger expense subtype (see chart_of_accounts.py)
LEDGER_SUBTYPE_BY_PLATFORM = {
    AdPlatform.META.value: "ad_spend_meta",
    AdPlatform.GOOGLE.value: "ad_spend_google",
    AdPlatform.TIKTOK.value: "ad_spend_tiktok",
    AdPlatform.OTHER.value: "ad_spend_other",
}

# platform -> ChannelPlatform enum value used by the connector registry
CHANNEL_PLATFORM_BY_PLATFORM = {
    AdPlatform.META.value: "meta_ads",
    AdPlatform.GOOGLE.value: "google_ads",
    AdPlatform.TIKTOK.value: "tiktok_ads",
}


class ReallocationStatus(str, enum.Enum):
    RECOMMENDED = "recommended"
    APPLIED = "applied"
    PARTIALLY_APPLIED = "partially_applied"
    REJECTED = "rejected"
    FAILED = "failed"
    NOOP = "noop"


class AdBudgetConfig(Base):
    __tablename__ = "ad_budget_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, unique=True, index=True)

    is_active = Column(Boolean, default=False, nullable=False)
    is_paused = Column(Boolean, default=False, nullable=False)
    paused_reason = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=True, nullable=False)

    # Guardrails
    total_daily_budget = Column(Numeric(14, 2), nullable=True)   # null -> keep sum of channel budgets
    optimization_window_days = Column(Integer, default=14, nullable=False)
    target_roas = Column(Numeric(8, 3), default=2.0, nullable=False)
    kill_roas = Column(Numeric(8, 3), default=0.7, nullable=False)
    min_channel_share = Column(Numeric(5, 4), default=0.10, nullable=False)   # learning floor
    max_daily_shift_pct = Column(Numeric(5, 4), default=0.25, nullable=False)
    aggressiveness = Column(Numeric(4, 2), default=1.5, nullable=False)       # exponent on ROAS weight
    allow_pause = Column(Boolean, default=False, nullable=False)
    min_data_conversions = Column(Integer, default=5, nullable=False)         # below -> treat as low-confidence

    currency = Column(String(3), default="ARS", nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(24), nullable=True)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AdChannel(Base):
    __tablename__ = "ad_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    channel_connection_id = Column(UUID(as_uuid=True), nullable=True)  # -> channel_connections.id (no FK: soft link)

    platform = Column(String(16), nullable=False)   # AdPlatform
    display_name = Column(String(120), nullable=False)

    current_daily_budget = Column(Numeric(14, 2), default=0, nullable=False)
    min_daily_budget = Column(Numeric(14, 2), nullable=True)
    max_daily_budget = Column(Numeric(14, 2), nullable=True)

    is_managed = Column(Boolean, default=True, nullable=False)   # autopilot may change its budget
    is_paused = Column(Boolean, default=False, nullable=False)

    campaign_refs = Column(JSONB, default=list, nullable=False)      # platform campaign IDs
    attribution_match = Column(JSONB, default=list, nullable=False)  # substrings vs order.source_campaign/source_channel

    currency = Column(String(3), default="ARS", nullable=False)
    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    snapshots = relationship("AdPerformanceSnapshot", back_populates="channel",
                             cascade="all, delete-orphan", lazy="noload")

    __table_args__ = (
        UniqueConstraint("business_id", "platform", "display_name",
                         name="uq_ad_channel_business_platform_name"),
        Index("ix_ad_channels_business_platform", "business_id", "platform"),
    )


class AdPerformanceSnapshot(Base):
    __tablename__ = "ad_performance_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    ad_channel_id = Column(UUID(as_uuid=True), ForeignKey("ad_channels.id", ondelete="CASCADE"),
                           nullable=False, index=True)

    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(16), default="ledger", nullable=False)   # connector | ledger

    spend = Column(Numeric(16, 2), default=0, nullable=False)
    revenue = Column(Numeric(16, 2), default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    impressions = Column(Integer, default=0, nullable=False)

    roas = Column(Numeric(10, 4), default=0, nullable=False)
    cpa = Column(Numeric(14, 2), nullable=True)
    recent_roas = Column(Numeric(10, 4), nullable=True)   # last third of window — trend signal

    captured_at = Column(DateTime(timezone=True), default=_utcnow)

    channel = relationship("AdChannel", back_populates="snapshots")

    __table_args__ = (
        Index("ix_ad_perf_channel_captured", "ad_channel_id", "captured_at"),
    )


class BudgetReallocation(Base):
    __tablename__ = "budget_reallocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    run_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    status = Column(String(20), default=ReallocationStatus.RECOMMENDED.value, nullable=False)
    blended_roas = Column(Numeric(10, 4), nullable=True)
    total_budget_before = Column(Numeric(16, 2), default=0, nullable=False)
    total_budget_after = Column(Numeric(16, 2), default=0, nullable=False)

    decisions = Column(JSONB, default=list, nullable=False)
    # [{ad_channel_id, platform, name, before, after, delta, delta_pct,
    #   roas, conversions, action, reason, applied, apply_error}]

    window_days = Column(Integer, default=14, nullable=False)
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    applied_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_budget_reallocations_business_created", "business_id", "created_at"),
    )


AD_BUDGET_TABLES = [
    AdBudgetConfig.__table__,
    AdChannel.__table__,
    AdPerformanceSnapshot.__table__,
    BudgetReallocation.__table__,
]
