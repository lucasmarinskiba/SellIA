"""Acquisition Strategist Agent Models"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class AcquisitionStrategy(Base):
    """Estrategia de adquisición de clientes completa."""
    __tablename__ = "acquisition_strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_name = Column(String(255), nullable=False)
    channels = Column(JSONB, default=list, nullable=False)  # [ChannelRecommendation, ...]
    funnel_stages = Column(JSONB, default=list, nullable=False)  # [{stage, conversion_rate, actions}, ...]
    cac_target = Column(Numeric(10, 2), nullable=True)
    ltv_target = Column(Numeric(10, 2), nullable=True)
    sequences = Column(JSONB, default=list, nullable=False)  # [{type, steps, channel}, ...]
    budget_allocation = Column(JSONB, default=dict, nullable=False)
    expected_results = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
