import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class KPIDashboard(Base):
    __tablename__ = "kpi_dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    dashboard_name = Column(String(255), nullable=False)
    widgets = Column(JSONB, default=list, nullable=False)
    refresh_interval = Column(Integer, default=300, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class KPIWidget(Base):
    __tablename__ = "kpi_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("kpi_dashboards.id", ondelete="CASCADE"), nullable=False, index=True)
    widget_type = Column(String(50), nullable=False)  # chart/metric/table
    title = Column(String(255), nullable=False)
    data_source = Column(String(255), nullable=False)
    config = Column(JSONB, default=dict, nullable=False)
    alerts = Column(JSONB, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
