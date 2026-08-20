"""Phase 39: Collaborative CRM."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class SalesWorkspace(Base):
    __tablename__ = "sales_workspaces"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class DealBoard(Base):
    __tablename__ = "deal_boards"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("sales_workspaces.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    board_name = Column(String(255), nullable=False)
    stages = Column(JSONB, nullable=False)  # [prospect, qualified, proposal, closed]
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class PipelineVisibility(Base):
    __tablename__ = "pipeline_visibility"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    total_opportunities = Column(Integer, default=0)
    total_pipeline_value = Column(Integer, default=0)
    win_rate = Column(Integer, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
