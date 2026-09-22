"""Webhook event models for real-time FOMO conversion tracking."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UUID as SQLUUID, Float, JSON, func
from pydantic import BaseModel

from app.core.database import Base

# Was its own private declarative_base(): the table was never created by
# schema_bootstrap.ensure_all_tables() (which only walks CoreBase.metadata), so
# every insert here 404'd on a missing relation. Moved onto CoreBase to actually
# get created. Table name is NOT `webhook_events` — that name is already taken on
# this same Base by app.domains.webhooks.webhook_models.WebhookEvent (outbound
# delivery log); reusing it would break configure_mappers() app-wide.


class WebhookEvent(Base):
  """Audit log for inbound generic conversion webhooks (POST .../webhooks/conversion)."""
  __tablename__ = 'seo_conversion_webhook_events'

  id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  business_id = Column(SQLUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
  platform = Column(String(50), nullable=False)
  event_type = Column(String(100), nullable=False)
  conversion_amount = Column(Float, nullable=True)
  payload = Column(JSON, nullable=False)
  ip_address = Column(String(45), nullable=True)
  # No signature scheme exists for this generic endpoint (unlike the ML webhook's
  # channel token) — 'unverified' always, never fabricate 'valid'.
  signature_valid = Column(String(12), default='unverified')
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
