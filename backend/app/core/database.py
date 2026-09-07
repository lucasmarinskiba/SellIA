from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import get_settings
from sqlalchemy.pool import NullPool

settings = get_settings()

# Build connect_args for SSL in production
connect_args = {}
if settings.ENVIRONMENT == "production" and settings.DB_SSL_MODE not in ("disable", "allow"):
    import ssl
    ssl_context = ssl.create_default_context()
    if settings.DB_SSL_MODE in ("verify-ca", "verify-full") and settings.DB_SSL_CA:
        ssl_context.load_verify_locations(settings.DB_SSL_CA)
    elif settings.DB_SSL_MODE in ("verify-ca", "verify-full"):
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        # require / prefer — verify server cert but don't require CA file
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

if settings.ENVIRONMENT == "testing" or is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        # Pool tuning for production load (PostgreSQL only)
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Sync companion engine, for the handful of call sites that genuinely can't
# be async -- Celery tasks (app/domains/auth/email_auth.py, app/domains/
# enterprise/{email_automation,psychology_sales,voice_sales}.py) run in a
# plain sync worker context with no event loop. Points at the same database
# via psycopg2 (already a dependency) instead of asyncpg. Prefer
# AsyncSessionLocal/get_db for anything that can be async -- this exists
# only because those 4 files' Celery tasks previously imported a
# `SessionLocal` that never existed anywhere in the codebase.
_sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
if settings.ENVIRONMENT == "testing" or is_sqlite:
    sync_engine = create_engine(_sync_database_url, poolclass=NullPool)
else:
    sync_engine = create_engine(_sync_database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
