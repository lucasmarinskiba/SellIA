"""Async SQLAlchemy engine + session factory + RLS tenant context."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.ENV == "dev",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Optionally create tables on startup. Use Alembic in prod."""
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    pass


async def close_engine() -> None:
    await engine.dispose()


@asynccontextmanager
async def get_session(tenant_id: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield AsyncSession with tenant context set for Postgres RLS.

    Postgres RLS policies should be defined like:

        CREATE POLICY tenant_isolation ON deals
            USING (tenant_id = current_setting('app.tenant_id')::uuid);

    We bind app.tenant_id per session so all queries are auto-filtered.
    """
    async with AsyncSessionLocal() as session:
        if tenant_id:
            # SET LOCAL only persists within current transaction
            await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
