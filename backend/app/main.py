"""
Single canonical entry point for all deployments (Docker CMD: uvicorn app.main:app).

Wraps the production app defined in app.sellbot (DB, scheduler, task processor,
rate limiting, structured logging, core /api/v1 routers) and additionally mounts
the auth/users/businesses/catalog/agents family of routers that only exist here.
Each extra router is mounted defensively: a missing dependency or broken import
in one domain must never take down the whole service.
"""
import logging

from app.sellbot import app  # noqa: F401  (re-exported below)

logger = logging.getLogger(__name__)


def _try_include(router_path: str, prefix: str, tags: list[str]) -> None:
    try:
        module_path, attr = router_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[attr])
        router = getattr(module, attr)
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"✅ Loaded extra router: {prefix} ({router_path})")
    except Exception as e:
        logger.warning(f"⚠️  Skipped extra router {prefix} ({router_path}): {e}")


# Extra routers carried over from the legacy main.py entry point.
# These use app.core.database / app.domains.* models (a separate ORM base
# from app.db.models) — their tables are provisioned via Alembic, not the
# sellbot lifespan's create_all.
_try_include("app.api.v1.whatsapp_webhook.router", "/api/v1", ["webhooks"])
_try_include("app.api.v1.email_sequences.router", "/api/v1", ["sequences"])
_try_include("app.api.v1.auth.router", "/api/v1/auth", ["auth"])
_try_include("app.api.v1.users.router", "/api/v1/users", ["users"])
_try_include("app.api.v1.businesses.router", "/api/v1/businesses", ["businesses"])
_try_include("app.domains.webhooks.router.router", "/api/v1", ["webhooks"])
_try_include("app.api.v1.conversations.router", "/api/v1/businesses", ["conversations"])
_try_include("app.api.v1.catalog.router", "/api/v1/catalog", ["catalog"])
_try_include("app.api.v1.subscriptions.router", "/api/v1/subscriptions", ["subscriptions"])
_try_include("app.api.v1.agents.router", "/api/v1/agents", ["agents"])
_try_include("app.api.v1.metadata.router", "/api/v1/metadata", ["metadata"])
_try_include("app.api.v1.embeddings.router", "/api/v1/embeddings", ["embeddings"])
_try_include("app.api.v1.analytics.router", "/api/v1/analytics", ["analytics"])
_try_include("app.api.v1.ml_optimization.router", "/api/v1/ml-optimization", ["ml-optimization"])
_try_include("app.api.v1.agent_orchestration.router", "/api/v1", ["agent-orchestration"])
_try_include("app.api.v1.negotiation.router", "/api/v1", ["negotiation"])
_try_include("app.api.v1.revenue_intelligence.router", "/api/v1", ["revenue-intelligence"])
_try_include("app.api.v1.ab_testing.router", "/api/v1", ["ab-testing"])
_try_include("app.api.v1.integrations.router", "/api/v1", ["integrations"])
_try_include("app.api.v1.business_intelligence.router", "/api/v1", ["business-intelligence"])
_try_include("app.api.v1.advanced_automation.router", "/api/v1", ["advanced-automation"])
_try_include("app.api.v1.lead_generation_agent.router", "/api/v1", ["lead-generation-agent"])
_try_include("app.api.v1.launch_scale.router", "/api/v1", ["launch-scale"])
_try_include("app.api.v1.coaching_adaptive.router", "/api/v1", ["coaching-adaptive"])
_try_include("app.api.v1.enterprise_analytics.router", "/api/v1", ["analytics-enterprise"])
_try_include("app.api.v1.enterprise_integrations.router", "/api/v1", ["integrations-enterprise"])
_try_include("app.api.v1.enterprise_teams.router", "/api/v1", ["teams-enterprise"])
_try_include("app.api.v1.enterprise_forecast.router", "/api/v1", ["forecast-enterprise"])


@app.get("/health", tags=["system"])
async def health_alias():
    """Liveness probe for the Docker HEALTHCHECK. See /api/health for full dependency status."""
    return {"status": "ok"}


__all__ = ["app"]
