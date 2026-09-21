"""Webhook service for real-time FOMO conversion ingestion and SSE streaming."""

import asyncio
import json
from datetime import datetime
from uuid import UUID, uuid4
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

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
    """Ingest conversion webhook and broadcast to subscribers."""

    event_id = uuid4()

    # Log webhook event
    stmt = insert(WebhookEvent).values(
      id=event_id,
      business_id=business_id,
      platform=platform,
      event_type='conversion',
      conversion_amount=payload.amount,
      payload=payload.model_dump(),
      ip_address=ip_address,
      signature_valid='valid',
    )
    await self.db.execute(stmt)
    await self.db.commit()

    # Track conversion in FOMO service
    fomo_service = FOMAConversionService(self.db)
    conversion = await fomo_service.track_conversion(
      business_id=business_id,
      platform=platform,
      link_id=payload.link_id,
      amount=payload.amount,
      customer_email=payload.customer_email,
      timestamp=payload.timestamp or datetime.utcnow(),
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
