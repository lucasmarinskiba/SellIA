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
_try_include("app.api.v1.resend_webhook.router", "/api/v1", ["webhooks"])
_try_include("app.api.v1.email_sequences.router", "/api/v1", ["sequences"])
_try_include("app.api.v1.auth.router", "/api/v1/auth", ["auth"])
_try_include("app.api.v1.users.router", "/api/v1/users", ["users"])
_try_include("app.api.v1.businesses.router", "/api/v1/businesses", ["businesses"])
_try_include("app.domains.businesses.locations_router.router", "/api/v1", ["locations"])
_try_include("app.domains.business_context.api.router", "/api/v1", ["business-context"])
_try_include("app.domains.agents.lead_qualifier.router.router", "/api/v1", ["lead-qualifier"])
_try_include("app.api.v1.bookings.router", "/api/v1", ["bookings"])
# payments.py's router already declares prefix="/api/v1" internally — pass "" here to avoid doubling it
_try_include("app.api.v1.payments.router", "", ["payments"])
_try_include("app.api.v1.offline_tracking.router", "/api/v1", ["offline-tracking"])
_try_include("app.api.v1.offline_bi.router", "/api/v1/bi", ["offline-bi"])
_try_include("app.api.v1.location_checkin.router", "/api/v1", ["location-checkin"])
_try_include("app.api.v1.location_qr.router", "/api/v1", ["location-qr"])
_try_include("app.api.v1.location_inventory.router", "/api/v1", ["inventory"])
_try_include("app.domains.channel_integration.router.router", "/api/v1", ["channel-integration"])
_try_include("app.api.v1.offline_sequences.router", "/api/v1", ["offline-sequences"])
_try_include("app.api.v1.websites.router", "/api/v1/websites", ["websites"])
_try_include("app.api.v1.seo.router", "/api/v1/seo", ["seo"])
_try_include("app.api.v1.analytics_tracking.router", "/api/v1", ["analytics"])
_try_include("app.api.v1.products.router", "/api/v1", ["products"])
_try_include("app.domains.webhooks.router.router", "/api/v1", ["webhooks"])
_try_include("app.api.v1.conversations.router", "/api/v1/businesses", ["conversations"])
_try_include("app.api.v1.brain_live.router", "/api/v1/brain", ["brain-live"])
_try_include("app.api.v1.proximity_tracking.router", "/api/v1", ["proximity"])
_try_include("app.api.v1.channels.router", "/api/v1/businesses", ["channels"])
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
_try_include("app.api.v1.enterprise_testing.router", "/api/v1", ["testing-enterprise"])
_try_include("app.api.v1.enterprise_knowledge.router", "/api/v1", ["knowledge-enterprise"])
_try_include("app.api.v1.enterprise_webhooks.router", "/api/v1", ["webhooks-enterprise"])
_try_include("app.api.v1.enterprise_collaboration.router", "/api/v1", ["collaboration-enterprise"])
_try_include("app.api.v1.enterprise_deal_intelligence.router", "/api/v1", ["intelligence-enterprise"])
_try_include("app.api.v1.enterprise_voice_agent.router", "/api/v1", ["voice-agent-enterprise"])
_try_include("app.api.v1.oauth_platforms.router", "/api/v1", ["oauth-platforms"])
_try_include("app.api.v1.seo_analyzer.router", "/api/v1", ["seo-analyzer"])
_try_include("app.api.v1.authority_building.router", "/api/v1", ["authority-building"])
_try_include("app.api.v1.team_collaboration.router", "/api/v1", ["team-collaboration"])
_try_include("app.api.v1.deal_intelligence.router", "/api/v1", ["deal-intelligence"])
_try_include("app.api.v1.revenue_orchestration.router", "/api/v1", ["revenue-orchestration"])
_try_include("app.api.v1.churn_prevention.router", "/api/v1", ["churn-prevention"])
_try_include("app.api.v1.marketplace_expansion.router", "/api/v1", ["marketplace-expansion"])
_try_include("app.api.v1.signup.router", "/api/v1", ["auth"])
_try_include("app.api.v1.dashboard.router", "/api/v1", ["dashboard"])
_try_include("app.api.v1.platforms.router", "/api/v1", ["platforms"])
_try_include("app.api.v1.order_detail.router", "/api/v1", ["orders"])
_try_include("app.api.v1.listings.router", "/api/v1", ["listings"])
_try_include("app.domains.finance.router.router", "/api/v1/businesses", ["finance"])
_try_include("app.domains.ledger.router.router", "/api/v1/businesses", ["ledger"])
_try_include("app.domains.ad_budget.router.router", "/api/v1/businesses", ["ad-budget"])
_try_include("app.domains.forecasting.router.router", "/api/v1/businesses", ["forecasting"])
_try_include("app.domains.cashflow.router.router", "/api/v1/businesses", ["cashflow"])
_try_include("app.domains.orchestrator.router.router", "/api/v1/businesses", ["orchestrator"])
_try_include("app.domains.hr.router.router", "/api/v1/businesses", ["hr"])
_try_include("app.domains.legal.router.router", "/api/v1/businesses", ["legal"])
_try_include("app.domains.procurement.router.router", "/api/v1/businesses", ["procurement"])
_try_include("app.domains.invoicing.router.router", "/api/v1/businesses", ["invoicing"])
_try_include("app.domains.seo_intelligence.router.router", "/api/v1/businesses", ["seo"])
_try_include("app.domains.fomo_seo.router.router", "/api/v1/businesses", ["fomo-seo"])
_try_include("app.domains.seo_optimization.router.router", "/api/v1/businesses", ["seo-optimization"])
_try_include("app.domains.seo_agents.router.router", "/api/v1/businesses", ["seo-agents"])
_try_include("app.domains.fomo.router.router", "", ["fomo"])
_try_include("app.domains.fomo.growth_foom_routes.router", "", ["growth-foom"])
_try_include("app.domains.fomo.customer_fomo_routes.router", "", ["customer-fomo"])
_try_include("app.domains.fomo.ai_copywriter_routes.router", "", ["fomo-ai-copywriter"])
_try_include("app.domains.fomo.ai_segmentation_routes.router", "", ["fomo-ai-segmentation"])
_try_include("app.domains.fomo.ai_timing_optimizer_routes.router", "", ["fomo-ai-timing"])


@app.get("/health", tags=["system"])
async def health_alias():
    """Liveness probe for the Docker HEALTHCHECK. See /api/health for full dependency status."""
    return {"status": "ok"}


__all__ = ["app"]
