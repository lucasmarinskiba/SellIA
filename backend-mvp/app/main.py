"""
SellIA Backend MVP · production skeleton.

Stack:
  - FastAPI (async)
  - SQLAlchemy 2.0 async + asyncpg
  - Multi-tenant via Row-Level Security (RLS) on PostgreSQL
  - JWT auth (PyJWT)
  - Stripe webhooks
  - WhatsApp Cloud API webhook
  - Redis (cache + queues)
  - Anthropic Claude SDK + Ollama fallback

Run:
  uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.observability import init_sentry
from app.db.session import close_engine, init_db
from app.api import (
    auth_router,
    tenants_router,
    deals_router,
    channels_router,
    billing_router,
    stripe_connect_router,
    onboarding_router,
    cua_sandbox_router,
    metrics_router,
    extension_auth_router,
    arca_router,
)
from app.channels.whatsapp import whatsapp_router
from app.channels.whatsapp_oauth import router as wa_oauth_router
from app.billing.stripe_webhook import stripe_webhook_router
from app.ws import ws_router


setup_logging()
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init DB + cache on startup, dispose on shutdown."""
    await init_db()
    yield
    await close_engine()


app = FastAPI(
    title="SellIA API",
    version="0.1.0",
    description="Brain-as-a-service · multi-tenant",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all so errors return JSON, not HTML stack traces."""
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": app.version}


# Mount routers
app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
app.include_router(tenants_router, prefix="/v1/tenants", tags=["tenants"])
app.include_router(deals_router, prefix="/v1/deals", tags=["deals"])
app.include_router(channels_router, prefix="/v1/channels", tags=["channels"])
app.include_router(billing_router, prefix="/v1/billing", tags=["billing"])
app.include_router(stripe_connect_router, prefix="/v1/connect", tags=["stripe-connect"])
app.include_router(onboarding_router, prefix="/v1/onboarding", tags=["onboarding"])
app.include_router(cua_sandbox_router, prefix="/v1/cua", tags=["cua-sandbox"])
app.include_router(wa_oauth_router, prefix="/v1/channels/whatsapp", tags=["wa-oauth"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
app.include_router(extension_auth_router, prefix="/v1/ext", tags=["extension-auth"])
app.include_router(arca_router, prefix="/v1/arca", tags=["arca"])

# Webhooks (no /v1 prefix, no auth — verified by signature)
app.include_router(stripe_webhook_router, prefix="/webhooks/stripe", tags=["webhooks"])
app.include_router(whatsapp_router, prefix="/webhooks/whatsapp", tags=["webhooks"])

# WebSocket
app.include_router(ws_router, prefix="/ws", tags=["websocket"])
