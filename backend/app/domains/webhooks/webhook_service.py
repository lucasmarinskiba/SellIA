"""Webhook & event streaming service."""

import logging
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.webhooks.webhook_models import (
    WebhookEndpoint, WebhookEvent, WebhookDeliveryLog, EventQueue, EventType
)

logger = logging.getLogger(__name__)


class WebhookService:
    """Manage webhooks and event delivery."""

    @staticmethod
    def register_webhook(
        business_id: UUID,
        url: str,
        subscribed_events: List[str],
        description: str = None,
        db: Session = None
    ) -> dict:
        """Register webhook endpoint."""
        if not db:
            raise ValueError("Database session required")

        secret_key = WebhookService._generate_secret()

        webhook = WebhookEndpoint(
            business_id=business_id,
            url=url,
            subscribed_events=subscribed_events,
            secret_key=secret_key,
            description=description
        )

        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        logger.info(f"Webhook registered: {url}")

        return {
            "webhook_id": str(webhook.id),
            "url": url,
            "secret_key": secret_key,
            "subscribed_events": subscribed_events
        }

    @staticmethod
    def _generate_secret() -> str:
        """Generate webhook secret key."""
        import secrets
        return secrets.token_urlsafe(32)

    @staticmethod
    def trigger_event(
        business_id: UUID,
        event_type: str,
        event_data: Dict,
        db: Session = None
    ) -> dict:
        """Trigger event and deliver to webhooks."""
        if not db:
            raise ValueError("Database session required")

        # Find subscribed webhooks
        webhooks = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.business_id == business_id,
            WebhookEndpoint.is_active == True
        ).all()

        delivered_count = 0
        for webhook in webhooks:
            if event_type not in webhook.subscribed_events:
                continue

            # Create event record
            signature = WebhookService._generate_signature(event_data, webhook.secret_key)

            event = WebhookEvent(
                business_id=business_id,
                endpoint_id=webhook.id,
                event_type=event_type,
                event_data=event_data,
                signature_hmac=signature
            )

            db.add(event)
            db.commit()

            # Deliver event
            WebhookService._deliver_event(webhook, event, db)
            delivered_count += 1

        logger.info(f"Event {event_type} delivered to {delivered_count} webhooks")

        return {
            "event_type": event_type,
            "webhooks_triggered": delivered_count
        }

    @staticmethod
    def _generate_signature(data: Dict, secret: str) -> str:
        """Generate HMAC-SHA256 signature."""
        payload = json.dumps(data, sort_keys=True)
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _deliver_event(
        webhook: WebhookEndpoint,
        event: WebhookEvent,
        db: Session = None
    ) -> bool:
        """Deliver webhook event with retries."""
        if not db:
            return False

        headers = {
            "X-Webhook-Signature": event.signature_hmac,
            "X-Webhook-Event": event.event_type,
            "Content-Type": "application/json"
        }

        try:
            response = httpx.post(
                webhook.url,
                json=event.event_data,
                headers=headers,
                timeout=10
            )

            log = WebhookDeliveryLog(
                webhook_event_id=event.id,
                business_id=event.business_id,
                attempt_number=event.delivery_attempts + 1,
                status_code=response.status_code,
                response_time_ms=int(response.elapsed.total_seconds() * 1000)
            )

            db.add(log)

            if response.status_code == 200:
                event.delivery_status = "delivered"
                webhook.success_count += 1
            else:
                event.delivery_status = "failed"
                webhook.failure_count += 1
                event.response_status_code = response.status_code
                event.response_body = response.text[:500]

            event.delivery_attempts += 1
            event.last_attempt_at = datetime.now(timezone.utc)
            webhook.last_fired_at = datetime.now(timezone.utc)

            db.commit()
            logger.info(f"Webhook delivered: {webhook.url} - {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Webhook delivery failed: {webhook.url} - {str(e)}")

            log = WebhookDeliveryLog(
                webhook_event_id=event.id,
                business_id=event.business_id,
                attempt_number=event.delivery_attempts + 1,
                error_message=str(e)
            )

            db.add(log)
            event.delivery_status = "failed"
            event.delivery_attempts += 1
            webhook.failure_count += 1
            db.commit()

            return False

    @staticmethod
    def queue_event(
        business_id: UUID,
        event_type: str,
        event_data: Dict,
        source: str = "api",
        db: Session = None
    ) -> dict:
        """Queue event for async processing."""
        if not db:
            raise ValueError("Database session required")

        event = EventQueue(
            business_id=business_id,
            event_type=event_type,
            event_source=source,
            event_data=event_data
        )

        db.add(event)
        db.commit()

        logger.info(f"Event queued: {event_type}")

        return {
            "event_id": str(event.id),
            "event_type": event_type,
            "status": "queued"
        }

    @staticmethod
    def get_webhook_stats(
        business_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get webhook delivery statistics."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        webhooks = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.business_id == business_id
        ).all()

        total_success = sum(w.success_count for w in webhooks)
        total_failure = sum(w.failure_count for w in webhooks)
        total_events = total_success + total_failure

        success_rate = (total_success / max(total_events, 1)) * 100

        return {
            "webhook_count": len(webhooks),
            "total_events": total_events,
            "successful_deliveries": total_success,
            "failed_deliveries": total_failure,
            "success_rate_pct": round(success_rate, 2),
            "avg_response_time_ms": sum(w.avg_response_time_ms for w in webhooks) // max(len(webhooks), 1)
        }
