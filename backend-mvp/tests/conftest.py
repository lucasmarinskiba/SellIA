"""Shared fixtures · async client + clean DB per test."""
import asyncio
import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test env BEFORE app import
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-32-bytes-of-padding-here")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-256-bits-padding-test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://sellia:sellia@localhost:5432/sellia_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

from app.db.models import Base  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine) -> AsyncIterator[AsyncSession]:
    Session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake_signup_payload() -> dict:
    rand = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{rand}@sellia.test",
        "password": "supersecret123",
        "name": f"Test User {rand}",
        "tenant_name": f"Test Tenant {rand}",
    }
