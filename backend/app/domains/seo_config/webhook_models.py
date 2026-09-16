"""Webhook event models for real-time FOMO conversion tracking."""

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, DateTime, UUID as SQLUUID, Float, JSON, func
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class WebhookEvent(Base):
  """Audit log for all incoming webhook events."""
  __tablename__ = 'webhook_events'

  id = Column(SQLUUID, primary_key=True, default=lambda: UUID('00000000-0000-0000-0000-000000000000'))
  business_id = Column(SQLUUID, nullable=False, index=True)
  platform = Column(String(50), nullable=False)
  event_type = Column(String(100), nullable=False)
  conversion_amount = Column(Float, nullable=True)
  payload = Column(JSON, nullable=False)
  ip_address = Column(String(45), nullable=True)
  signature_valid = Column(String(10), default='pending')
  created_at = Column(DateTime, server_default=func.now(), index=True)


# ── Pydantic Schemas ──
class ConversionWebhookPayload(BaseModel):
  """Generic conversion webhook payload."""
  platform: str
  link_id: str | None = None
  customer_email: str | None = None
  customer_phone: str | None = None
  amount: float | None = None
  timestamp: datetime | None = None
  metadata: dict[str, str] | None = None


class MercadoLibreWebhookPayload(BaseModel):
  """MercadoLibre webhook format."""
  resource: str
  action: str
  topic: str
  timestamp: datetime | None = None
  data: dict[str, object] | None = None


class WebhookEventResponse(BaseModel):
  """Response for webhook ingestion."""
  received: bool
  message: str
  event_id: str | None = None
  class Config:
    from_attributes = True
