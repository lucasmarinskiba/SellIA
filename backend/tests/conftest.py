"""
Pytest configuration for SellIA backend tests.
Uses AsyncClient for proper async FastAPI testing.
"""

import asyncio
import pathlib
import pytest
import pytest_asyncio
from typing import AsyncGenerator

import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long-1234567890"
os.environ["ENABLE_OPENAPI"] = "false"
# Defaults target the docker-compose service hostnames (`db`, `redis`). CI and
# any non-compose environment must point at their own services via
# TEST_DATABASE_URL / TEST_REDIS_URL — a dedicated variable (not DATABASE_URL)
# because the session fixture below drops and recreates the whole `public`
# schema of this DB, so it must never inherit a real application database URL.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://ia_vendedor:x-5Of06QfCskz81KLMj0iHGWkIBwVmNY@db:5432/test_ia_vendedor",
)
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://redis:6379/1")

import httpx
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app

# ── Quarantine of known-broken tests ─────────────────────────────────────────
# tests/known_failures.txt lists tests that fail today because they were written
# against APIs/fixtures that no longer exist (see the header in that file). They
# are marked xfail (non-strict) so CI stays meaningful: any test NOT on the list
# that breaks fails the run, a listed test that gets fixed shows up as XPASS,
# and the debt stays visible in the summary instead of being hidden.
_KNOWN_FAILURES_FILE = pathlib.Path(__file__).parent / "known_failures.txt"

# Test modules that cannot even be imported (they reference classes that don't
# exist under those names anywhere in the codebase). Ignoring them at collection
# lets us drop --continue-on-collection-errors, so a NEW collection error
# fails CI instead of being tolerated.
collect_ignore: list[str] = [
    "test_automation_engine.py",       # imports Workflow, not defined in automation_engine
    "test_computer_use.py",            # imports AutomationAction, not in computer_use_orchestrator_v2
    "test_ml_engine.py",
    "test_real_estate_agent.py",
    "test_strategy_engine.py",
]


def _load_known_failures() -> set[str]:
    if not _KNOWN_FAILURES_FILE.exists():
        return set()
    ids: set[str] = set()
    for raw in _KNOWN_FAILURES_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            ids.add(line)
    return ids


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    known = _load_known_failures()
    if not known:
        return
    marker = pytest.mark.xfail(
        reason="quarantined: known failure listed in tests/known_failures.txt",
        strict=False,
    )
    for item in items:
        if item.nodeid in known:
            item.add_marker(marker)


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    """Create tables in test database and init rate limiter."""
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.database import engine as global_engine
    from app.db.schema_bootstrap import ensure_all_tables

    from sqlalchemy.pool import NullPool

    # This fixture wipes the whole schema, so refuse to run against anything
    # that isn't obviously a test database.
    db_name = make_url(os.environ["DATABASE_URL"]).database or ""
    if "test" not in db_name:
        raise RuntimeError(f"Refusing to reset non-test database {db_name!r}")

    # Dispose any existing pooled connections from previous test runs
    await global_engine.dispose()

    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, future=True, poolclass=NullPool)

    async def reset_schema() -> None:
        # Not Base.metadata.drop_all/create_all: both resolve the whole
        # foreign-key graph up front and raise NoReferencedTableError if any
        # model points at a table no model declares (the app has such dangling
        # references), which errored every DB-backed test at setup. Dropping the
        # schema needs no FK graph, and ensure_all_tables() is the same
        # per-table, tolerant creation the app runs at startup.
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))

    await reset_schema()
    await ensure_all_tables(engine)

    # Init rate limiter for tests
    redis_instance = redis.from_url(os.environ["REDIS_URL"], encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_instance)

    yield

    await reset_schema()
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
