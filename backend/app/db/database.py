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
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        raise

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
