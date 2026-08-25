from fastapi import APIRouter, Query, Body
from app.domains.enterprise.webhooks import WebhookManager, WebhookEvent, IntegrationProvider

router = APIRouter(tags=["webhooks"])
webhook_manager = WebhookManager()


@router.post("/webhooks/create")
async def create_webhook(
    user_id: str = Query(...),
    name: str = Query(...),
    event: str = Query(...),
    target_url: str = Query(...),
    provider: str = Query("custom_webhook"),
):
    """Create webhook integration."""
    try:
        event_enum = WebhookEvent(event)
        provider_enum = IntegrationProvider(provider)

        webhook = webhook_manager.create_webhook(
            user_id, name, event_enum, target_url, provider_enum
        )

        return {
            "status": "created",
            "webhook_id": webhook.id,
            "name": name,
            "event": event,
            "provider": provider,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@router.get("/webhooks/list/{user_id}")
async def list_webhooks(user_id: str):
    """List all webhooks."""
    webhooks = webhook_manager.get_webhooks(user_id)

    return {
        "user_id": user_id,
        "total": len(webhooks),
        "webhooks": [
            {
                "id": wh.id,
                "name": wh.name,
                "event": wh.event.value,
                "provider": wh.provider.value,
                "active": wh.is_active,
                "trigger_count": wh.trigger_count,
                "last_triggered": wh.last_triggered_at.isoformat() if wh.last_triggered_at else None,
            }
            for wh in webhooks
        ],
    }


@router.post("/webhooks/{webhook_id}/trigger")
async def trigger_webhook(
    user_id: str = Query(...),
    webhook_id: str = Query(...),
    payload: dict = Body(...),
):
    """Manually trigger webhook (test)."""
    success = webhook_manager.trigger_webhook(user_id, webhook_id, payload)

    return {
        "status": "triggered" if success else "not_found",
        "webhook_id": webhook_id,
    }


@router.get("/webhooks/{webhook_id}/logs")
async def get_webhook_logs(
    user_id: str = Query(...),
    webhook_id: str = Query(...),
    limit: int = Query(50, le=100),
):
    """Get webhook execution logs."""
    logs = webhook_manager.get_webhook_logs(user_id, webhook_id, limit)

    return {
        "webhook_id": webhook_id,
        "total_logs": len(logs),
        "logs": [
            {
                "id": log.id,
                "event": log.event.value,
                "status": "success" if log.success else "failed",
                "triggered_at": log.triggered_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.post("/webhooks/zapier/setup")
async def setup_zapier(
    user_id: str = Query(...),
    zapier_webhook_url: str = Query(...),
    events: list[str] = Body(...),
):
    """Setup Zapier integration."""
    try:
        # Validate events
        for event in events:
            WebhookEvent(event)

        integration = webhook_manager.setup_zapier(user_id, zapier_webhook_url, events)

        return {
            "status": "configured",
            "provider": "zapier",
            "webhook_url": zapier_webhook_url,
            "events": events,
            "active": integration.is_active,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@router.get("/webhooks/zapier/{user_id}")
async def get_zapier_integration(user_id: str):
    """Get Zapier integration status."""
    integration = webhook_manager.get_zapier_integration(user_id)

    if not integration:
        return {"status": "not_configured"}

    return {
        "status": "configured",
        "provider": "zapier",
        "active": integration.is_active,
        "events": [e.value for e in integration.enabled_events],
        "trigger_count": integration.trigger_count,
        "created_at": integration.created_at.isoformat(),
    }


@router.get("/webhooks/stats/{user_id}")
async def get_webhook_stats(user_id: str):
    """Get webhook integration statistics."""
    stats = webhook_manager.get_integration_stats(user_id)

    return {
        "user_id": user_id,
        "statistics": {
            "total_webhooks": stats["total_webhooks"],
            "active_webhooks": stats["active_webhooks"],
            "zapier_configured": stats["zapier_configured"],
            "total_triggers": stats["total_triggers"],
            "success_rate": f"{stats['success_rate']}%",
        },
    }
