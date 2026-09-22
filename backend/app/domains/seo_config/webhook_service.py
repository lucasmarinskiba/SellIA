"""Webhook service for real-time FOMO conversion ingestion and SSE streaming."""

import asyncio
import json
from datetime import datetime
from uuid import UUID, uuid4
from typing import AsyncGenerator
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.seo_config.models import PublicationLink
from app.domains.seo_config.webhook_models import WebhookEvent, ConversionWebhookPayload
from app.domains.seo_config.fomo_service import FOMAConversionService


class WebhookService:
  """Handles webhook ingestion, validation, and event streaming."""

  def __init__(self, db: AsyncSession):
    self.db = db
    self._subscribers: dict[str, list[asyncio.Queue]] = {}

  async def ingest_conversion(
    self,
    business_id: UUID,
    platform: str,
    payload: ConversionWebhookPayload,
    ip_address: str | None = None,
  ) -> dict[str, object]:
    """Ingest conversion webhook and broadcast to subscribers.

    ConversionEvent.link_id is NOT NULL and the caller-supplied link_id is
    untrusted input, so it's resolved against this business's own publication
    links first. A link_id that's missing, unowned, or fabricated by the
    caller never reaches FOMAConversionService — it's logged for audit
    (event_type='conversion_unmatched') but not counted as a conversion.
    """

    event_id = uuid4()
    link = None
    if payload.link_id:
      try:
        link_uuid = UUID(payload.link_id)
      except ValueError:
        link_uuid = None
      if link_uuid:
        result = await self.db.execute(
          select(PublicationLink).where(
            PublicationLink.id == link_uuid,
            PublicationLink.business_id == business_id,
          )
        )
        link = result.scalar_one_or_none()

    # Log webhook event — audit trail only, this endpoint has no signature
    # scheme (unlike the Mercado Libre channel-token webhook), so it's always
    # 'unverified', never fabricated as 'valid'.
    stmt = insert(WebhookEvent).values(
      id=event_id,
      business_id=business_id,
      platform=platform,
      event_type='conversion' if link else 'conversion_unmatched',
      conversion_amount=payload.amount,
      payload=payload.model_dump(mode="json"),
      ip_address=ip_address,
      signature_valid='unverified',
    )
    await self.db.execute(stmt)
    await self.db.commit()

    if not link:
      return {
        'received': True,
        'message': 'link_id ausente o no pertenece a este negocio — evento registrado, conversión no contabilizada',
        'event_id': str(event_id),
      }

    fomo_service = FOMAConversionService(self.db)
    await fomo_service.log_conversion(
      business_id=business_id,
      link_id=link.id,
      platform_name=platform,
      conversion_type='purchase',
      conversion_value=payload.amount or 0.0,
      raw_event_data=payload.model_dump(mode="json"),
    )

    # Broadcast to all subscribers (real-time push)
    await self._broadcast_event(business_id, 'conversion', {
      'id': str(event_id),
      'platform': platform,
      'amount': payload.amount,
      'email': payload.customer_email,
      'timestamp': (payload.timestamp or datetime.utcnow()).isoformat(),
    })

    return {
      'received': True,
      'message': 'Conversion tracked',
      'event_id': str(event_id),
    }

  async def _broadcast_event(
    self,
    business_id: UUID,
    event_type: str,
    data: dict[str, object],
  ) -> None:
    """Broadcast event to all subscribers for a business."""
    key = str(business_id)
    if key not in self._subscribers:
      return

    event_json = json.dumps({
      'type': event_type,
      'data': data,
      'timestamp': datetime.utcnow().isoformat(),
    })

    for queue in self._subscribers[key]:
      try:
        queue.put_nowait(event_json)
      except asyncio.QueueFull:
        pass

  async def subscribe(self, business_id: UUID) -> AsyncGenerator[str, None]:
    """Subscribe to real-time events for a business (SSE stream)."""
    key = str(business_id)
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=50)

    if key not in self._subscribers:
      self._subscribers[key] = []
    self._subscribers[key].append(queue)

    try:
      while True:
        try:
          event = await asyncio.wait_for(queue.get(), timeout=30.0)
          yield f'data: {event}\n\n'
        except asyncio.TimeoutError:
          yield ': heartbeat\n\n'
    finally:
      self._subscribers[key].remove(queue)
      if not self._subscribers[key]:
        del self._subscribers[key]
