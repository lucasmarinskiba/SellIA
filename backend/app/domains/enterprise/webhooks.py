from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class WebhookEvent(str, Enum):
    LEAD_CREATED = "lead.created"
    LEAD_CONVERTED = "lead.converted"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    MESSAGE_SENT = "message.sent"
    COACHING_COMPLETED = "coaching.completed"
    TEST_COMPLETED = "test.completed"
    FORECAST_UPDATED = "forecast.updated"


class IntegrationProvider(str, Enum):
    ZAPIER = "zapier"
    MAKE = "make"
    INTEGROMAT = "integromat"
    CUSTOM_WEBHOOK = "custom_webhook"
    SLACK = "slack"
    MICROSOFT_TEAMS = "teams"


@dataclass
class Webhook:
    id: str
    name: str
    event: WebhookEvent
    target_url: str
    provider: IntegrationProvider
    is_active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    retry_count: int = 0
    headers: dict = field(default_factory=dict)


@dataclass
class WebhookLog:
    id: str
    webhook_id: str
    event: WebhookEvent
    payload: dict
    response_status: int
    response_body: str
    triggered_at: datetime
    success: bool


@dataclass
class ZapierIntegration:
    user_id: str
    zapier_webhook_url: str
    enabled_events: list[WebhookEvent]
    is_active: bool
    created_at: datetime
    trigger_count: int = 0


class WebhookManager:
    def __init__(self):
        self.webhooks = {}
        self.logs = {}
        self.zapier_integrations = {}

    def create_webhook(
        self,
        user_id: str,
        name: str,
        event: WebhookEvent,
        target_url: str,
        provider: IntegrationProvider,
    ) -> Webhook:
        webhook = Webhook(
            id=f"wh_{datetime.now().timestamp()}",
            name=name,
            event=event,
            target_url=target_url,
            provider=provider,
            is_active=True,
            created_at=datetime.now(),
        )

        key = f"{user_id}:{webhook.id}"
        self.webhooks[key] = webhook
        return webhook

    def trigger_webhook(
        self,
        user_id: str,
        webhook_id: str,
        payload: dict,
        response_status: int = 200,
    ) -> bool:
        key = f"{user_id}:{webhook_id}"
        if key not in self.webhooks:
            return False

        webhook = self.webhooks[key]
        webhook.trigger_count += 1
        webhook.last_triggered_at = datetime.now()

        log = WebhookLog(
            id=f"whl_{datetime.now().timestamp()}",
            webhook_id=webhook_id,
            event=webhook.event,
            payload=payload,
            response_status=response_status,
            response_body="OK" if response_status == 200 else "ERROR",
            triggered_at=datetime.now(),
            success=response_status == 200,
        )

        log_key = f"{user_id}:{log.id}"
        self.logs[log_key] = log
        return True

    def get_webhooks(self, user_id: str) -> list[Webhook]:
        return [
            wh for k, wh in self.webhooks.items()
            if k.startswith(f"{user_id}:")
        ]

    def get_webhook_logs(self, user_id: str, webhook_id: str, limit: int = 50) -> list[WebhookLog]:
        logs = [
            log for k, log in self.logs.items()
            if k.startswith(f"{user_id}:") and log.webhook_id == webhook_id
        ]
        return sorted(logs, key=lambda x: x.triggered_at, reverse=True)[:limit]

    def setup_zapier(
        self,
        user_id: str,
        zapier_webhook_url: str,
        events: list[str],
    ) -> ZapierIntegration:
        integration = ZapierIntegration(
            user_id=user_id,
            zapier_webhook_url=zapier_webhook_url,
            enabled_events=[WebhookEvent(e) for e in events],
            is_active=True,
            created_at=datetime.now(),
        )

        key = f"{user_id}:zapier"
        self.zapier_integrations[key] = integration
        return integration

    def get_zapier_integration(self, user_id: str) -> Optional[ZapierIntegration]:
        key = f"{user_id}:zapier"
        return self.zapier_integrations.get(key)

    def get_integration_stats(self, user_id: str) -> dict:
        webhooks = self.get_webhooks(user_id)
        zapier = self.get_zapier_integration(user_id)

        total_triggers = sum(wh.trigger_count for wh in webhooks)
        successful_triggers = sum(
            len([log for log in self.get_webhook_logs(user_id, wh.id) if log.success])
            for wh in webhooks
        )

        success_rate = (
            (successful_triggers / total_triggers * 100)
            if total_triggers > 0 else 0
        )

        return {
            "total_webhooks": len(webhooks),
            "active_webhooks": len([wh for wh in webhooks if wh.is_active]),
            "zapier_configured": zapier is not None,
            "total_triggers": total_triggers,
            "success_rate": round(success_rate, 1),
        }
