"""Sentry init · structured error reporting."""
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry if DSN configured. No-op in dev w/o DSN."""
    if not settings.SENTRY_DSN:
        logger.info("sentry_disabled · no DSN")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENV,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
            ],
            traces_sample_rate=0.10 if settings.ENV == "prod" else 1.0,
            profiles_sample_rate=0.05 if settings.ENV == "prod" else 0,
            send_default_pii=False,  # privacy first
            attach_stacktrace=True,
            release=f"sellia@0.1.0",
        )
        logger.info("sentry_initialized", extra={"env": settings.ENV})
    except ImportError:
        logger.warning("sentry_sdk_not_installed")
    except Exception as e:
        logger.exception("sentry_init_failed", extra={"error": str(e)})
