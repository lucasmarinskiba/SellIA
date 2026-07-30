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
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Default: use SQLite for local testing
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    logger.warning(f"DATABASE_URL not set, using SQLite: {DATABASE_URL}")

# ============================================================
# ENGINE & SESSION
# ============================================================
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=NullPool if DATABASE_URL.startswith("sqlite") else None
)

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
