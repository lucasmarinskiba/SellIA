"""Persistence for deal-outcome accuracy tracking.

The only piece of app/domains/enterprise/forecasting.py's original design
that genuinely needs a durable record: everything else (deal scores, pipeline
forecasts, risk lists) is now computed live from real app.domains.crm.models.
Deal rows on every request, which is more correct than a cache anyway (it
can never go stale) -- but a "we forecasted X% win probability, the deal
actually won/lost" outcome IS a historical event that should be recorded
once and kept, for win-rate/accuracy reporting over time.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class DealOutcome(Base):
    """A recorded win/loss outcome for a deal, for forecast-accuracy tracking."""
    __tablename__ = "deal_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome = Column(String(10), nullable=False)  # won, lost
    final_value = Column(Numeric(14, 2), nullable=True)
    days_to_close = Column(Integer, nullable=True)
    forecasted_probability = Column(Numeric(5, 4), nullable=False)  # 0.0-1.0, what we predicted before the outcome
    forecast_accuracy = Column(Numeric(5, 4), nullable=False)  # 1 - |forecasted - actual|
    win_loss_reason = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_deal_outcomes_business", "business_id", "recorded_at"),
    )
