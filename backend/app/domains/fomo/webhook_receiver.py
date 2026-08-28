"""FOMO Webhook Receiver - Ingest real-time events from customer websites"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import hashlib
import hmac
import json
from decimal import Decimal


class WebhookEventType(str, Enum):
    VISITOR_ARRIVED = "visitor.arrived"
    VISITOR_LEFT = "visitor.left"
    PURCHASE_COMPLETED = "purchase.completed"
    CART_ABANDONED = "cart.abandoned"
    CART_RECOVERED = "cart.recovered"
    PAGE_VIEWED = "page.viewed"
    PRODUCT_VIEWED = "product.viewed"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT_STARTED = "checkout.started"
    CHECKOUT_COMPLETED = "checkout.completed"
    REVIEW_POSTED = "review.posted"
    WISHLIST_ADDED = "wishlist.added"


class WebhookPayload:
    """Validate and parse incoming webhook payloads"""

    @staticmethod
    def validate_signature(
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature (HMAC-SHA256)"""
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    @staticmethod
    def parse_event(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize webhook event"""
        return {
            "event_type": data.get("type"),
            "campaign_id": data.get("campaign_id"),
            "user_id": data.get("user_id"),
            "session_id": data.get("session_id"),
            "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            "data": {
                "product_id": data.get("product_id"),
                "product_name": data.get("product_name"),
                "product_price": Decimal(str(data.get("price", 0))),
                "quantity": data.get("quantity", 1),
                "order_value": Decimal(str(data.get("order_value", 0))),
                "customer_email": data.get("customer_email"),
                "customer_name": data.get("customer_name"),
                "page_url": data.get("page_url"),
                "referrer": data.get("referrer"),
                "ip_address": data.get("ip_address"),
                "user_agent": data.get("user_agent"),
                "custom_data": data.get("custom_data", {}),
            }
        }


class WebhookProcessor:
    """Process incoming FOMO webhook events"""

    @staticmethod
    async def process_visitor_arrived(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle visitor.arrived event"""
        return {
            "event_id": event.get("session_id"),
            "campaign_id": event.get("campaign_id"),
            "event_type": "visitor",
            "action": "increment_counter",
            "value": 1,
            "broadcast": True,
            "widgets_affected": ["visitor_counter"],
            "analytics": {
                "impressions": 1,
                "timestamp": event.get("timestamp"),
            }
        }

    @staticmethod
    async def process_purchase_completed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle purchase.completed event - trigger purchase notification widget"""
        data = event.get("data", {})
        return {
            "event_id": f"{event.get('session_id')}_purchase",
            "campaign_id": event.get("campaign_id"),
            "event_type": "purchase",
            "action": "show_notification",
            "notification": {
                "message": f"{data.get('customer_name', 'Alguien')} acaba de comprar {data.get('product_name')}",
                "customer_name": data.get("customer_name"),
                "product_name": data.get("product_name"),
                "price": float(data.get("product_price", 0)),
                "anonymized": False,
            },
            "broadcast": True,
            "widgets_affected": ["purchase_feed"],
            "analytics": {
                "conversions": 1,
                "revenue": float(data.get("order_value", 0)),
                "timestamp": event.get("timestamp"),
            }
        }

    @staticmethod
    async def process_cart_abandoned(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cart.abandoned event - trigger recovery automations"""
        data = event.get("data", {})
        return {
            "event_id": f"{event.get('session_id')}_abandoned",
            "campaign_id": event.get("campaign_id"),
            "event_type": "cart_abandonment",
            "action": "trigger_automation",
            "automation_type": "cart_abandonment",
            "user_data": {
                "email": data.get("customer_email"),
                "name": data.get("customer_name"),
                "cart_value": float(data.get("order_value", 0)),
                "products": data.get("products", []),
            },
            "delay_minutes": 5,
            "broadcast": False,
            "automation_sequence": [
                {
                    "step": 1,
                    "delay_minutes": 0,
                    "channel": "email",
                    "template": "cart_abandoned_1",
                },
                {
                    "step": 2,
                    "delay_minutes": 120,
                    "channel": "email",
                    "template": "cart_abandoned_2_social_proof",
                },
                {
                    "step": 3,
                    "delay_minutes": 1440,
                    "channel": "sms",
                    "template": "cart_abandoned_3_final_discount",
                },
            ]
        }

    @staticmethod
    async def process_cart_recovered(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cart.recovered event - celebrate recovery"""
        data = event.get("data", {})
        return {
            "event_id": f"{event.get('session_id')}_recovered",
            "campaign_id": event.get("campaign_id"),
            "event_type": "cart_recovery",
            "action": "cancel_automation",
            "automation_type": "cart_abandonment",
            "analytics": {
                "conversions": 1,
                "revenue": float(data.get("order_value", 0)),
                "recovery_source": data.get("recovery_source", "unknown"),  # email/sms/direct
                "timestamp": event.get("timestamp"),
            }
        }

    @staticmethod
    async def process_page_viewed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle page.viewed event"""
        data = event.get("data", {})
        return {
            "event_id": f"{event.get('session_id')}_pageview",
            "campaign_id": event.get("campaign_id"),
            "event_type": "pageview",
            "action": "track_engagement",
            "page_url": data.get("page_url"),
            "widgets_active": ["all"],  # All widgets on page are impressed
            "analytics": {
                "impressions": 1,
                "timestamp": event.get("timestamp"),
            }
        }

    @staticmethod
    async def process_checkout_completed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout.completed event"""
        data = event.get("data", {})
        return {
            "event_id": f"{event.get('session_id')}_checkout",
            "campaign_id": event.get("campaign_id"),
            "event_type": "checkout",
            "action": "record_conversion",
            "conversion_type": "purchase",
            "analytics": {
                "conversions": 1,
                "revenue": float(data.get("order_value", 0)),
                "average_order_value": float(data.get("order_value", 0)),
                "timestamp": event.get("timestamp"),
            }
        }


class WebhookQuota:
    """Rate limiting for webhooks"""

    @staticmethod
    def get_quota_limits(plan_tier: str) -> Dict[str, int]:
        """Get webhook quota limits by plan tier"""
        limits = {
            "starter": {
                "events_per_day": 10000,
                "events_per_minute": 100,
                "concurrent_webhooks": 10,
            },
            "pro": {
                "events_per_day": 100000,
                "events_per_minute": 1000,
                "concurrent_webhooks": 50,
            },
            "pro_plus": {
                "events_per_day": 500000,
                "events_per_minute": 5000,
                "concurrent_webhooks": 100,
            },
            "founder": {
                "events_per_day": 2000000,
                "events_per_minute": 20000,
                "concurrent_webhooks": 500,
            },
            "enterprise": {
                "events_per_day": 10000000,
                "events_per_minute": 100000,
                "concurrent_webhooks": 1000,
            },
        }
        return limits.get(plan_tier, limits["starter"])

    @staticmethod
    def check_quota(
        campaign_id: str,
        plan_tier: str,
        events_today: int,
        events_this_minute: int,
    ) -> Dict[str, Any]:
        """Check if webhook quota exceeded"""
        limits = WebhookQuota.get_quota_limits(plan_tier)

        daily_exceeded = events_today >= limits["events_per_day"]
        minute_exceeded = events_this_minute >= limits["events_per_minute"]

        return {
            "allowed": not (daily_exceeded or minute_exceeded),
            "reason": "daily_limit" if daily_exceeded else ("minute_limit" if minute_exceeded else None),
            "current_daily": events_today,
            "limit_daily": limits["events_per_day"],
            "current_minute": events_this_minute,
            "limit_minute": limits["events_per_minute"],
        }


class WebhookRetry:
    """Retry logic for failed webhook deliveries"""

    @staticmethod
    def get_retry_schedule() -> List[Dict[str, Any]]:
        """Get exponential backoff retry schedule"""
        return [
            {"attempt": 1, "delay_seconds": 5, "description": "First retry after 5 seconds"},
            {"attempt": 2, "delay_seconds": 30, "description": "Second retry after 30 seconds"},
            {"attempt": 3, "delay_seconds": 300, "description": "Third retry after 5 minutes"},
            {"attempt": 4, "delay_seconds": 1800, "description": "Fourth retry after 30 minutes"},
            {"attempt": 5, "delay_seconds": 3600, "description": "Fifth retry after 1 hour"},
        ]

    @staticmethod
    def should_retry(
        http_status_code: int,
        attempts: int,
    ) -> bool:
        """Determine if webhook delivery should be retried"""
        # Don't retry client errors (4xx)
        if 400 <= http_status_code < 500:
            return False

        # Retry server errors and timeouts (5xx)
        if http_status_code >= 500:
            return attempts < 5

        # Retry network timeouts
        return attempts < 5
