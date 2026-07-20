"""
Monitoring Setup — Alerts + Dashboards + Logging.

Integraciones:
- Datadog (APM + metrics)
- Sentry (error tracking)
- PagerDuty (incident management)
- Slack (notifications)
"""

import logging
import time
from functools import wraps
from typing import Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ========== DATADOG SETUP ==========

def setup_datadog():
    """Configura Datadog para APM + metrics."""

    try:
        from datadog import initialize, api
        from datadog.api import metrics

        options = {
            "api_key": "DATADOG_API_KEY",
            "app_key": "DATADOG_APP_KEY",
        }
        initialize(**options)

        logger.info("Datadog initialized")
        return True

    except ImportError:
        logger.warning("Datadog not installed. Install: pip install datadog")
        return False


def track_metric(metric_name: str, value: float, tags: list = None):
    """
    Envía métrica a Datadog.

    Ejemplos:
    - track_metric("sellias.orders.count", 5)
    - track_metric("sellias.revenue", 250.50, tags=["channel:mercadolibre"])
    """

    try:
        from datadog import api

        api.Metric.send(
            metric=metric_name,
            points=value,
            tags=tags or [],
        )

    except Exception as e:
        logger.error(f"Datadog metric failed: {str(e)}")


# ========== SENTRY SETUP ==========

def setup_sentry():
    """Configura Sentry para error tracking."""

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn="SENTRY_DSN",
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0,
            environment="production",
        )

        logger.info("Sentry initialized")
        return True

    except ImportError:
        logger.warning("Sentry not installed. Install: pip install sentry-sdk")
        return False


def track_exception(exc: Exception, extra: dict = None):
    """
    Reporta excepción a Sentry.

    Ejemplos:
    - track_exception(e, extra={"order_id": "123"})
    """

    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)

        if extra:
            with sentry_sdk.push_scope() as scope:
                for key, value in extra.items():
                    scope.set_extra(key, value)

    except Exception as e:
        logger.error(f"Sentry tracking failed: {str(e)}")


# ========== PERFORMANCE MONITORING ==========

def monitor_performance(func: Callable) -> Callable:
    """
    Decorator que trackea performance de function.

    @monitor_performance
    async def create_checkout(...):
        ...

    Trackea: latency, errors, count
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        try:
            result = await func(*args, **kwargs)

            latency = (time.time() - start_time) * 1000  # ms
            track_metric(f"sellias.function.latency", latency, tags=[f"function:{func_name}"])
            track_metric(f"sellias.function.success", 1, tags=[f"function:{func_name}"])

            if latency > 1000:  # Si > 1 segundo
                logger.warning(f"{func_name} took {latency:.0f}ms")

            return result

        except Exception as e:
            track_metric(f"sellias.function.error", 1, tags=[f"function:{func_name}"])
            track_exception(e, extra={"function": func_name})
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        try:
            result = func(*args, **kwargs)

            latency = (time.time() - start_time) * 1000
            track_metric(f"sellias.function.latency", latency, tags=[f"function:{func_name}"])
            track_metric(f"sellias.function.success", 1, tags=[f"function:{func_name}"])

            if latency > 1000:
                logger.warning(f"{func_name} took {latency:.0f}ms")

            return result

        except Exception as e:
            track_metric(f"sellias.function.error", 1, tags=[f"function:{func_name}"])
            track_exception(e, extra={"function": func_name})
            raise

    # Detectar async/sync
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# ========== ALERTS ==========

class AlertManager:
    """Maneja alertas via Slack + PagerDuty."""

    def __init__(self, slack_webhook: str = None, pagerduty_token: str = None):
        self.slack_webhook = slack_webhook
        self.pagerduty_token = pagerduty_token

    async def alert_high_error_rate(self, error_rate: float):
        """Alerta si error rate > 5%."""

        if error_rate > 0.05:
            await self._send_alert(
                level="critical",
                title="High Error Rate",
                message=f"Error rate: {error_rate:.1%}. Investigating...",
            )

    async def alert_api_latency(self, latency_ms: float):
        """Alerta si API latency > 1 segundo."""

        if latency_ms > 1000:
            await self._send_alert(
                level="warning",
                title="API Latency High",
                message=f"API p95 latency: {latency_ms:.0f}ms",
            )

    async def alert_payment_failure(self, order_id: str, amount: float):
        """Alerta si payment falla."""

        await self._send_alert(
            level="critical",
            title="Payment Failure",
            message=f"Order {order_id}: ${amount} payment failed. Check Stripe.",
        )

    async def alert_database_down(self):
        """Alerta si database caída."""

        await self._send_alert(
            level="critical",
            title="Database Down",
            message="Database unreachable. On-call paging...",
        )

    async def alert_webhook_failure(self, webhook_name: str, error: str):
        """Alerta si webhook falla."""

        await self._send_alert(
            level="warning",
            title=f"Webhook Failure: {webhook_name}",
            message=f"Error: {error}",
        )

    async def _send_alert(self, level: str, title: str, message: str):
        """Envía alert a Slack + PagerDuty."""

        # Slack
        if self.slack_webhook:
            color = {"critical": "danger", "warning": "warning", "info": "good"}[level]
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "SellIA Monitoring",
                        "ts": int(time.time()),
                    }
                ]
            }

            import httpx
            try:
                await httpx.AsyncClient().post(self.slack_webhook, json=payload)
            except Exception as e:
                logger.error(f"Slack alert failed: {str(e)}")

        # PagerDuty (si critical)
        if level == "critical" and self.pagerduty_token:
            await self._trigger_pagerduty_incident(title, message)

    async def _trigger_pagerduty_incident(self, title: str, message: str):
        """Trigger PagerDuty incident."""

        import httpx

        payload = {
            "routing_key": self.pagerduty_token,
            "event_action": "trigger",
            "dedup_key": f"sellias_{int(time.time())}",
            "payload": {
                "summary": title,
                "severity": "critical",
                "source": "SellIA Monitoring",
                "custom_details": {"message": message},
            },
        }

        try:
            await httpx.AsyncClient().post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
            )
        except Exception as e:
            logger.error(f"PagerDuty trigger failed: {str(e)}")


# ========== HEALTH CHECK ==========

async def health_check_database() -> bool:
    """Verifica database connectivity."""

    try:
        from sqlalchemy import text
        from backend.app.core.database import get_db

        async with get_db() as db:
            await db.execute(text("SELECT 1"))
        return True

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


async def health_check_stripe() -> bool:
    """Verifica Stripe API."""

    try:
        import stripe
        stripe.Account.retrieve()
        return True

    except Exception as e:
        logger.error(f"Stripe health check failed: {str(e)}")
        return False


async def health_check_mercadolibre() -> bool:
    """Verifica Mercado Libre API."""

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.mercadolibre.com/sites/MLA")
            return resp.status_code == 200

    except Exception as e:
        logger.error(f"ML health check failed: {str(e)}")
        return False


async def health_check_all() -> dict:
    """Full system health check."""

    return {
        "database": await health_check_database(),
        "stripe": await health_check_stripe(),
        "mercadolibre": await health_check_mercadolibre(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ========== SETUP FUNCTION ==========

def setup_monitoring():
    """Inicializa todo monitoring."""

    logger.info("Setting up monitoring...")

    # Datadog
    setup_datadog()

    # Sentry
    setup_sentry()

    # Alerts
    alert_manager = AlertManager(
        slack_webhook="SLACK_WEBHOOK_URL",
        pagerduty_token="PAGERDUTY_INTEGRATION_KEY",
    )

    logger.info("Monitoring setup complete")

    return alert_manager
