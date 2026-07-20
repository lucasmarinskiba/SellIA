"""API routers."""
from app.api.auth import router as auth_router
from app.api.tenants import router as tenants_router
from app.api.deals import router as deals_router
from app.api.channels import router as channels_router
from app.api.billing import router as billing_router
from app.api.stripe_connect import router as stripe_connect_router
from app.api.onboarding import router as onboarding_router
from app.api.cua_sandbox import router as cua_sandbox_router
from app.api.metrics import router as metrics_router
from app.api.extension_auth import router as extension_auth_router
from app.api.arca import router as arca_router

__all__ = [
    "auth_router",
    "tenants_router",
    "deals_router",
    "channels_router",
    "billing_router",
    "stripe_connect_router",
    "onboarding_router",
    "cua_sandbox_router",
    "metrics_router",
    "extension_auth_router",
    "arca_router",
]
