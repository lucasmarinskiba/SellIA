"""Tests for SEO Intelligence — isolated SQLite."""

import json
import os
import uuid
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(el, comp, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(el, comp, **kw):  # noqa: ANN001
    return "TEXT"


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (
    lambda v: None if v is None else (_try_uuid(v))
)
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)


def _try_uuid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


from app.core.database import Base  # noqa: E402

# Import models directly to avoid circular imports
from app.domains.seo_intelligence.models import SEO_TABLES  # noqa: E402
from app.domains.seo_intelligence.service import (  # noqa: E402
    KeywordService,
    PageOptimizationService,
)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.tables["businesses"].create(bind=c, checkfirst=True))
        for t in SEO_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


class TestKeywordService:
    """Test keyword research."""

    @pytest.mark.asyncio
    async def test_add_keyword(self, db: AsyncSession):
        """Add keyword."""
        business_id = uuid4()
        svc = KeywordService(db)

        kw = await svc.add_keyword(
            business_id,
            "python web development",
            search_volume=12000,
            difficulty=45,
            cpc=Decimal("2.50"),
            competition="high",
            intent="commercial",
            trend="rising",
            platform="google",
        )

        assert kw.keyword == "python web development"
        assert kw.search_volume == 12000
        assert kw.difficulty == 45
        assert kw.trend == "rising"

    @pytest.mark.asyncio
    async def test_list_keywords(self, db: AsyncSession):
        """List keywords."""
        business_id = uuid4()
        svc = KeywordService(db)

        # Add keywords
        await svc.add_keyword(business_id, "seo optimization", 5000)
        await svc.add_keyword(business_id, "digital marketing", 8000)
        await svc.add_keyword(business_id, "content strategy", 3000)

        keywords = await svc.list_keywords(business_id)

        assert len(keywords) == 3
        # Ordered by search volume descending
        assert keywords[0].search_volume == 8000

    @pytest.mark.asyncio
    async def test_trending_keywords(self, db: AsyncSession):
        """Get trending keywords."""
        business_id = uuid4()
        svc = KeywordService(db)

        await svc.add_keyword(business_id, "stable keyword", 1000, trend="stable")
        await svc.add_keyword(business_id, "rising keyword", 500, trend="rising")
        await svc.add_keyword(business_id, "rising keyword 2", 300, trend="rising")

        trending = await svc.get_trending_keywords(business_id)

        assert len(trending) == 2
        assert all(kw.trend == "rising" for kw in trending)


class TestPageOptimization:
    """Test page SEO optimization."""

    @pytest.mark.asyncio
    async def test_create_page(self, db: AsyncSession):
        """Create page."""
        business_id = uuid4()
        svc = PageOptimizationService(db)

        page = await svc.create_page(
            business_id,
            "https://example.com/product",
            "Best Python Web Framework",
            "product",
            "Learn the top Python web framework for 2024",
            ["python", "web development", "django"],
        )

        assert page.page_url == "https://example.com/product"
        assert page.page_type == "product"
        assert page.indexed == False

    @pytest.mark.asyncio
    async def test_update_page_metrics(self, db: AsyncSession):
        """Update page metrics."""
        business_id = uuid4()
        svc = PageOptimizationService(db)

        page = await svc.create_page(
            business_id,
            "https://example.com/blog",
            "SEO Guide",
            "blog",
        )

        updated = await svc.update_page(
            page.id,
            page_speed_ms=1500,
            mobile_score=85,
            optimization_score=78,
            organic_traffic_30d=2500,
            organic_revenue_30d=Decimal("1250.00"),
        )

        assert updated.page_speed_ms == 1500
        assert updated.mobile_score == 85
        assert updated.optimization_score == 78
        assert updated.organic_traffic_30d == 2500

    @pytest.mark.asyncio
    async def test_seo_health(self, db: AsyncSession):
        """Get SEO health."""
        business_id = uuid4()
        svc = PageOptimizationService(db)

        # Create pages
        page1 = await svc.create_page(business_id, "https://example.com/1", "Page 1", "product")
        page2 = await svc.create_page(business_id, "https://example.com/2", "Page 2", "blog")

        # Update metrics
        await svc.update_page(page1.id, optimization_score=90, organic_traffic_30d=1000)
        await svc.update_page(page2.id, optimization_score=70, organic_traffic_30d=500)

        health = await svc.seo_health(business_id)

        assert health["total_pages"] == 2
        assert health["overall_score"] == 80  # (90 + 70) / 2
        assert health["organic_traffic_30d"] == 1500
