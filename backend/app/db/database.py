"""
Database initialization and session management.
PostgreSQL + SQLAlchemy async.
"""
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.db.models import Base
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE CONFIG
# ============================================================
def _normalize_async_url(url: str) -> str:
    """Force an async-capable driver scheme for SQLAlchemy's async engine.

    Render (and most hosts) hand out plain postgres://... / postgresql://...
    URLs, which SQLAlchemy resolves to the sync psycopg2 driver. create_async_engine
    then raises InvalidRequestError before the app can even start. Rewrite the
    scheme so the async driver (asyncpg) is always used, regardless of what the
    platform's connection string says.
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://"):]
    return url

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Default: use SQLite for local testing
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    logger.warning(f"DATABASE_URL not set, using SQLite: {DATABASE_URL}")
else:
    DATABASE_URL = _normalize_async_url(DATABASE_URL)

# ============================================================
# ENGINE & SESSION
# ============================================================
is_sqlite = DATABASE_URL.startswith("sqlite")
engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}
if is_sqlite:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# ============================================================
# INIT DATABASE
# ============================================================
async def init_db():
    """Create all tables on startup."""
    try:
        # Import all domain models to register them with CoreBase
        try:
            from app.domains.users import models as _  # noqa
            from app.domains.businesses import models as _  # noqa
            from app.domains.locations import models as _  # noqa
            from app.domains.orders import models as _  # noqa
            from app.domains.channels import models as _  # noqa
            from app.domains.analytics import models as _  # noqa
        except Exception as e:
            logger.warning(f"Some domain models failed to import (non-critical): {e}")

        async with engine.begin() as conn:
            # Create tables for app.db.models Base (safe subset)
            try:
                await conn.run_sync(Base.metadata.create_all)
            except Exception as e:
                logger.warning(f"Failed to create app.db tables: {e}")

            # Create tables for app.core.database Base (domains models).
            # Re-enabled: create_all() only CREATES missing tables, it never
            # touches ones that already exist, so this is safe to run even
            # though most of these tables were originally created by hand and
            # have since drifted from their ORM definitions (see the
            # business_contexts/2FA/audit-log patch blocks above/below for
            # that separate, ongoing problem). Without this, brand-new tables
            # introduced by any domain model (e.g. booking_events) would
            # never get created at all in production.
            try:
                from app.core.database import Base as CoreBase
                await conn.run_sync(CoreBase.metadata.create_all)
                logger.info("✅ CoreBase domain tables ensured")
            except Exception as e:
                logger.warning(f"Failed to create domain tables: {e}")

            logger.info("✅ Database initialization checked (migrations recommended)")
    except Exception as e:
        logger.error(f"⚠️  Database init warning: {e}")
        # Don't raise - allow app to start even if table creation fails
        # Tables should be created via migrations

async def get_db():
    """Dependency: get DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def close_db():
    """Close DB connection on shutdown."""
    await engine.dispose()
    logger.info("✅ Database connection closed")

# ============================================================
# MIGRATION PATH
# ============================================================
# TODO: Alembic migrations for FASE 3+
# Currently: SQLAlchemy auto-creates tables
# For production:
#   pip install alembic
#   alembic init alembic
#   alembic revision --autogenerate
#   alembic upgrade head
