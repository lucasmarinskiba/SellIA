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
_try_include("app.domains.ai_activity.api.router", "/api/v1", ["ai-activity"])
_try_include("app.domains.web_presence.api.router", "/api/v1", ["web-presence"])
_try_include("app.domains.data_science.api.router", "/api/v1", ["data-science"])
_try_include("app.api.v1.channel_setup.router", "/api/v1", ["channel-setup"])
_try_include("app.domains.integrations.api.router", "/api/v1", ["integrations-status"])
_try_include("app.domains.authority.api.router", "/api/v1", ["authority-builder"])
_try_include("app.domains.platform_commerce.api.router", "/api/v1", ["platform-commerce"])
_try_include("app.domains.chatbots.api.router", "/api/v1", ["chatbots"])
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
# brain.router's own routes already start with "/brain/..." (graph, activity,
# flows, cua/dispatch, capabilities, snapshot, overview, sales-team), so it
# mounts at bare /api/v1, not /api/v1/brain -- this was never wired into any
# app entrypoint before now, so the real capability registry it serves
# (app.core.brain) has been completely unreachable: BrainInteractionMap.tsx's
# fetchGraph() always failed and silently fell back to a static bundled
# snapshot, and EnterpriseCommandCenter.tsx's Computer Use dispatch button
# was hitting a 404. No path collisions with brain_live's routes above (its
# only overlapping name, kpis, was removed from brain.router -- see its
# top-of-file note).
_try_include("app.api.v1.brain.router", "/api/v1", ["brain-registry"])
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
# enterprise_webhooks.router removed: pure in-memory mock (fake Webhook/
# WebhookLog dataclasses, nothing ever delivered), 100% superseded by the
# real app.domains.webhooks system (HMAC-signed delivery, real DB, wired at
# /api/v1/webhooks) which is now actually triggered from real events -- see
# app/domains/webhooks/service.py's fire_business_event().
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
_try_include("app.api.v1.memory.router", "/api/v1/memory", ["memory"])
_try_include("app.api.v1.dashboard.router", "/api/v1", ["dashboard"])
_try_include("app.api.v1.platforms.router", "/api/v1", ["platforms"])
# app.api.v1.order_detail used to be mounted here. It was a mock: every one of
# its four endpoints returned invented data -- a hardcoded "iPhone 15 Pro" order
# for "Juan López", a note that was never stored, a confirmation email that was
# never sent, a cancellation that cancelled nothing -- and nothing in the
# frontend called it. Worse, its GET /orders/{order_id} sat in front of the real
# router and swallowed every other GET under /orders, including the spreadsheet.
# Deleted, so /orders is served only by the code that touches the database.
_try_include("app.domains.orders.router.router", "/api/v1", ["orders-domain"])
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
_try_include("app.domains.brand_transformation.router.router", "/api/v1/businesses", ["brand-transformation"])
_try_include("app.domains.financial_dashboard.router.router", "/api/v1/businesses", ["financial-dashboard"])
_try_include("app.domains.fomo.router.router", "", ["fomo"])
_try_include("app.domains.fomo.growth_foom_routes.router", "", ["growth-foom"])
_try_include("app.domains.fomo.customer_fomo_routes.router", "", ["customer-fomo"])
_try_include("app.domains.fomo.ai_copywriter_routes.router", "", ["fomo-ai-copywriter"])
_try_include("app.domains.fomo.ai_segmentation_routes.router", "", ["fomo-ai-segmentation"])
_try_include("app.domains.fomo.ai_timing_optimizer_routes.router", "", ["fomo-ai-timing"])
_try_include("app.domains.fomo.ai_scarcity_calibration_routes.router", "", ["fomo-ai-scarcity"])
_try_include("app.domains.fomo.ai_churn_prevention_routes.router", "", ["fomo-ai-churn"])
_try_include("app.domains.fomo.ai_autonomous_campaign_routes.router", "", ["fomo-ai-autonomous"])
_try_include("app.domains.fomo.ai_competitor_monitor_routes.router", "", ["fomo-ai-competitor"])
_try_include("app.domains.fomo.ai_orchestrator_routes.router", "", ["fomo-ai-orchestrator"])
# trade_signals: supervised copy-trade — agent proposes, user approves, backend
# never executes. Had a full test suite (tests/test_trade_signals_api.py) but
# was never actually mounted; every request 404'd. See that file's fixture
# docstring for the related get_store/Redis test-isolation fix.
_try_include("app.api.v1.trade_signals.router", "/api/v1/computer-use", ["trade-signals"])

# The Computer Use domain (app/domains/computer_use, ~80 files/17.7k lines:
# session management, platform automation scripts, browser control, lead
# scoring, ad orchestration, task scheduling, webhooks) has 8 dedicated API
# router files -- none of them were ever included anywhere (main.py or
# sellbot.py). /brain/cua/dispatch's own "can_execute" hint has been telling
# users to "usá /api/v1/computer_use/sessions para ejecutar" this whole time,
# and that route has never existed in production. Verified zero method+path
# collisions across all 8 files before mounting them together at the same
# prefix. Each _try_include is independent and best-effort (logs + skips on
# import failure rather than crashing boot), so a broken one doesn't take
# down the others -- exactly what surfaces which of these 8 are actually
# import-clean vs still broken, the same way it did for the enterprise_*
# cluster earlier this session.
_try_include("app.api.v1.computer_use.router", "/api/v1/computer_use", ["computer-use-sessions"])
_try_include("app.api.v1.computer_use_extended.router", "/api/v1/computer_use", ["computer-use-extended"])
_try_include("app.api.v1.computer_use_ad_orchestrator.router", "/api/v1/computer_use", ["computer-use-ads"])
_try_include("app.api.v1.computer_use_audit_log.router", "/api/v1/computer_use", ["computer-use-audit"])
_try_include("app.api.v1.computer_use_brain.router", "/api/v1/computer_use", ["computer-use-brain"])
_try_include("app.api.v1.computer_use_lead_scoring.router", "/api/v1/computer_use", ["computer-use-lead-scoring"])
_try_include("app.api.v1.computer_use_task_scheduler.router", "/api/v1/computer_use", ["computer-use-tasks"])
_try_include("app.api.v1.computer_use_webhooks.router", "/api/v1/computer_use", ["computer-use-webhooks"])

# "Phase 33" cluster: every file below failed to import for a mechanical
# reason (a `from backend.app...` path that only ever worked if the repo
# root were itself importable as a package named `backend`, which it isn't
# -- `app` is the real top-level package) until this session's fixes. All
# already declare their own full prefix, so pass "" here (same pattern as
# payments.py above). api/v1/payments_real.py is deliberately NOT included:
# it targets Account/Order models that live in an isolated, never-bootstrapped
# database schema (app/core/database/{models,payment_models}.py -- note that
# whole directory has no __init__.py, so it was never even reachable as
# app.core.database.X to begin with), needs Stripe/SendGrid credentials that
# were never added to settings, and duplicates the checkout flow the app
# actually uses (MercadoPago via api/v1/subscriptions.py) -- reviving it
# means inventing a second payment provider and a new Account concept from
# scratch, a product decision rather than a bug fix.
_try_include("app.api.v1.sales_cycle.router", "", ["sales-cycle"])
_try_include("app.api.v1.bulk_sales.router", "", ["bulk-sales"])
_try_include("app.api.v1.super_seller.router", "", ["super-seller"])
_try_include("app.api.v1.autonomous.router", "", ["autonomous"])
_try_include("app.api.v1.intelligence.router", "", ["intelligence"])
_try_include("app.api.v1.churn_retention.router", "", ["churn-retention"])
_try_include("app.api.v1.fomo_system.router", "", ["foom-system"])
_try_include("app.api.v1.foom_monetization.router", "", ["foom-monetization"])
_try_include("app.api.v1.platform_monetization.router", "", ["platform-monetization"])
_try_include("app.api.v1.psychology_sales.router", "", ["psychology-sales"])
_try_include("app.api.v1.voice_sales.router", "", ["voice-sales"])
_try_include("app.api.v1.platform_integration.router", "", ["platform-integration"])


@app.get("/health", tags=["system"])
async def health_alias():
    """Liveness probe for the Docker HEALTHCHECK. See /api/health for full dependency status."""
    return {"status": "ok"}


__all__ = ["app"]
