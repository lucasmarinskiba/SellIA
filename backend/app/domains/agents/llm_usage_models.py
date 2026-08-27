"""Per-business daily LLM call tracking (Task 6 — spend/runaway-usage cap).

One row per (business_id, usage_date), incremented on every LLM call that
actually goes out. Deliberately a call counter, not a cost tracker — see
BusinessContext.llm_daily_call_limit in business_context/models.py for why.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class LLMDailyUsage(Base):
    __tablename__ = "llm_daily_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False)
    call_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("business_id", "usage_date", name="uq_llm_daily_usage_business_date"),
    )
