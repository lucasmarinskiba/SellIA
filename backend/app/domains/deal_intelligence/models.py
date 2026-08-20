"""Phase 37: Deal Intelligence."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class WinLossAnalysis(Base):
    __tablename__ = "win_loss_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    outcome = Column(String(20), nullable=False)  # won, lost
    analysis = Column(String(2000), nullable=True)
    key_factors = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CompetitiveIntelligence(Base):
    __tablename__ = "competitive_intelligence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    intel_data = Column(JSONB, nullable=True)
    threat_level = Column(String(20), default="medium")
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class DealVelocity(Base):
    __tablename__ = "deal_velocity"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    avg_days_to_close = Column(Float, default=0)
    velocity_forecast = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
