"""
Entry point for all deployments.
Loads what's available; skips broken modules gracefully.
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SellIA backend starting...")
    # Redis / rate limiting — optional
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url and not redis_url.startswith("redis://localhost"):
        try:
            import redis.asyncio as redis
            from fastapi_limiter import FastAPILimiter
            r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await FastAPILimiter.init(r)
            logger.info("Rate limiter initialized")
        except Exception as e:
            logger.warning(f"Rate limiter skipped: {e}")
    yield
    logger.info("SellIA backend shutting down...")


app = FastAPI(
    title="SellIA Backend",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse(url="/api/ping")


@app.get("/api/ping")
async def ping():
    return {"status": "ok"}


@app.get("/health")
async def health():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    checks: dict = {"status": "ok"}

    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        try:
            engine = create_async_engine(db_url, pool_pre_ping=True)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {str(e)[:80]}"
            checks["status"] = "degraded"
    else:
        checks["database"] = "not configured"

    status_code = 200 if checks["status"] == "ok" else 503
    return JSONResponse(content=checks, status_code=status_code)


# Load routers that work — skip any that fail
def try_include(router_path: str, prefix: str, tags: list):
    try:
        parts = router_path.rsplit(".", 1)
        module = __import__(parts[0], fromlist=[parts[1]])
        router = getattr(module, parts[1])
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"Loaded: {prefix}")
    except Exception as e:
        logger.warning(f"Skipped {prefix}: {e}")


try_include("app.api.v1.whatsapp_webhook.router", "/api/v1", ["webhooks"])
try_include("app.api.v1.email_sequences.router", "/api/v1", ["sequences"])
try_include("app.api.v1.auth.router", "/api/v1/auth", ["auth"])
try_include("app.api.v1.users.router", "/api/v1/users", ["users"])
try_include("app.api.v1.businesses.router", "/api/v1/businesses", ["businesses"])
try_include("app.domains.webhooks.router.router", "/api/v1", ["webhooks"])
try_include("app.api.v1.conversations.router", "/api/v1/businesses", ["conversations"])
try_include("app.api.v1.catalog.router", "/api/v1/catalog", ["catalog"])
try_include("app.api.v1.subscriptions.router", "/api/v1/subscriptions", ["subscriptions"])
try_include("app.api.v1.agents.router", "/api/v1/agents", ["agents"])
try_include("app.api.v1.analytics.router", "/api/v1", ["analytics"])
