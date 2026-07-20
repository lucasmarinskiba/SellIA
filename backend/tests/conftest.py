"""
Pytest configuration for SellIA backend tests.
Uses AsyncClient for proper async FastAPI testing.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long-1234567890"
os.environ["ENABLE_OPENAPI"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ia_vendedor:x-5Of06QfCskz81KLMj0iHGWkIBwVmNY@db:5432/test_ia_vendedor"
os.environ["REDIS_URL"] = "redis://redis:6379/1"

import httpx
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    """Create tables in test database and init rate limiter."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.database import Base, engine as global_engine
    
    from sqlalchemy.pool import NullPool
    
    # Dispose any existing pooled connections from previous test runs
    await global_engine.dispose()
    
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, future=True, poolclass=NullPool)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Init rate limiter for tests
    redis_instance = redis.from_url(os.environ["REDIS_URL"], encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_instance)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    await redis_instance.aclose()


@pytest_asyncio.fixture
async def async_client(setup_test_db) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for FastAPI app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Async database session for tests."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from app.core.database import AsyncSessionLocal
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, future=True, poolclass=NullPool)
    AsyncTestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user in the database."""
    from app.domains.users.models import User
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email=f"test-extended-{uuid4()}@example.com",
        hashed_password="hashed",
        full_name="Test User Extended",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Generate auth headers for the test user."""
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_client(async_client, test_user):
    """Async HTTP client with authenticated user override."""
    from app.core.deps import get_current_active_user
    from app.main import app
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    yield async_client
    app.dependency_overrides.clear()
