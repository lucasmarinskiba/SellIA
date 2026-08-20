"""Phase 34: Sales AI Agents."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class ProspectingAgent(Base):
    __tablename__ = "prospecting_agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)  # linkedin, twitter, crunchbase, custom
    search_criteria = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class QualificationAgent(Base):
    __tablename__ = "qualification_agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    qualification_score = Column(Float, default=0)
    qualification_reason = Column(String(500), nullable=True)
    recommended_next_step = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ClosingAgent(Base):
    __tablename__ = "closing_agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    closing_probability = Column(Float, default=0)
    next_best_action = Column(String(255), nullable=True)
    objection_handling_tips = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
