"""Integration marketplace models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class IntegrationApp(Base):
    __tablename__ = "integration_apps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False)  # crm, email, sms, ecommerce, accounting
    
    app_id = Column(String(100), unique=True, nullable=False)
    webhook_url = Column(String(500), nullable=True)
    
    auth_type = Column(String(50), default="oauth")  # oauth, api_key, webhook
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    app_id = Column(UUID(as_uuid=True), ForeignKey("integration_apps.id", ondelete="CASCADE"), nullable=False)
    
    connection_status = Column(String(50), default="active")  # active, inactive, error
    
    auth_token = Column(String(1000), nullable=True)
    auth_metadata = Column(JSONB, nullable=True)
    
    last_sync_at = Column(DateTime(timezone.utc), nullable=True)
    last_error = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False)
    
    event_type = Column(String(100), nullable=False)  # order.created, customer.updated, etc
    event_data = Column(JSONB, nullable=False)
    
    sync_status = Column(String(50), default="pending")  # pending, synced, failed
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    synced_at = Column(DateTime(timezone.utc), nullable=True)
