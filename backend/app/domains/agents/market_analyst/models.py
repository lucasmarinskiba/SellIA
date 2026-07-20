"""Market Analyst Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class MarketAnalysisJob(Base):
    """Job que orquesta un análisis de mercado completo."""
    __tablename__ = "market_analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | running | completed | failed
    target_market = Column(String(255), nullable=False)
    competitors_analyzed = Column(Integer, nullable=False, default=0)
    trends_found = Column(Integer, nullable=False, default=0)
    report_url = Column(String(500), nullable=True)
    report_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    snapshots = relationship("CompetitorSnapshot", back_populates="job", cascade="all, delete-orphan")


class CompetitorSnapshot(Base):
    """Snapshot de un competidor dentro de un análisis."""
    __tablename__ = "competitor_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("market_analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    price_range = Column(String(100), nullable=True)
    key_features = Column(JSONB, default=list, nullable=False)
    strengths = Column(JSONB, default=list, nullable=False)
    weaknesses = Column(JSONB, default=list, nullable=False)
    sentiment_score = Column(Numeric(3, 2), nullable=True)  # -1.00 to 1.00
    raw_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job = relationship("MarketAnalysisJob", back_populates="snapshots")
