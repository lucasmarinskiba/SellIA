"""Tests for FOMO+SEO — isolated SQLite."""

import json
import os
import uuid
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

# Import models directly
from app.domains.fomo_seo.models import FOMO_SEO_TABLES  # noqa: E402
from app.domains.fomo_seo.service import FOMOSEOCopyService, A_B_TestService  # noqa: E402


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
        for t in FOMO_SEO_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


class TestFOMOSEOCopy:
    """Test FOMO+SEO copy generation."""

    @pytest.mark.asyncio
    async def test_generate_copy(self, db: AsyncSession):
        """Generate copy."""
        business_id = uuid4()
        product_id = uuid4()
        svc = FOMOSEOCopyService(db)

        copy = await svc.generate_copy(
            business_id,
            product_id,
            title="Limited Edition Python Web Framework - Save 50% Today",
            meta_description="Discover the proven Python web framework trusted by 10,000+ developers",
            short_description="Revolutionary web framework",
            long_description="The most advanced Python framework for building scalable web apps.",
            call_to_action="Grab Your Copy Now",
            urgency_trigger="limited_stock",
            social_proof_element="10,000+ developers trust us",
            scarcity_message="Only 5 licenses left at this price",
            keywords_targeted=["python web framework", "django alternative", "fast python"],
            platform="shopify",
        )

        assert copy.title == "Limited Edition Python Web Framework - Save 50% Today"
        assert copy.urgency_trigger == "limited_stock"
        assert copy.seo_score > 0
        assert copy.ctr_score > 50  # Should have high CTR with power words + urgency

    @pytest.mark.asyncio
    async def test_seo_score_calculation(self, db: AsyncSession):
        """Test SEO score calculation."""
        business_id = uuid4()
        svc = FOMOSEOCopyService(db)

        # Good title length + good meta + keywords
        copy = await svc.generate_copy(
            business_id,
            None,
            title="Best Python Web Framework for 2024",  # 43 chars (optimal 50-60)
            meta_description="Discover the proven Python web framework trusted by developers. Free trial.",  # 75 chars
            short_description="Best framework",
            long_description="Excellent for building apps",
            keywords_targeted=["python", "web", "framework"],
        )

        assert copy.seo_score > 50  # Should score well

    @pytest.mark.asyncio
    async def test_ctr_score_calculation(self, db: AsyncSession):
        """Test CTR score calculation."""
        business_id = uuid4()
        svc = FOMOSEOCopyService(db)

        # With power words + urgency
        copy = await svc.generate_copy(
            business_id,
            None,
            title="Guaranteed Results - Limited Time Offer",
            meta_description="Test",
            short_description="Test",
            long_description="Test",
            urgency_trigger="ending_soon",
            social_proof_element="Best seller",
        )

        assert copy.ctr_score > 70  # High CTR with power words + urgency + social proof

    @pytest.mark.asyncio
    async def test_list_copy(self, db: AsyncSession):
        """List copy variants."""
        business_id = uuid4()
        svc = FOMOSEOCopyService(db)

        for i in range(3):
            await svc.generate_copy(
                business_id,
                None,
                title=f"Title {i}",
                meta_description=f"Meta {i}",
                short_description="Short",
                long_description="Long",
                platform="shopify",
            )

        copies = await svc.list_copy(business_id)

        assert len(copies) == 3


class TestA_B_Test:
    """Test A/B testing."""

    @pytest.mark.asyncio
    async def test_create_test(self, db: AsyncSession):
        """Create A/B test."""
        business_id = uuid4()
        copy_id = uuid4()
        svc = A_B_TestService(db)

        test = await svc.create_test(
            business_id,
            copy_id,
            variant_a_title="Save Money Today",
            variant_b_title="Limited Time Offer - Save 50%",
            variant_a_description="Best product",
            variant_b_description="Exclusive deal for smart shoppers",
        )

        assert test.variant_a_title == "Save Money Today"
        assert test.variant_b_title == "Limited Time Offer - Save 50%"
        assert test.is_active == True

    @pytest.mark.asyncio
    async def test_update_results(self, db: AsyncSession):
        """Update test results."""
        business_id = uuid4()
        copy_id = uuid4()
        svc = A_B_TestService(db)

        test = await svc.create_test(
            business_id,
            copy_id,
            variant_a_title="Title A",
            variant_b_title="Title B",
            variant_a_description="Desc A",
            variant_b_description="Desc B",
        )

        # Variant B wins (higher conversion)
        updated = await svc.update_results(
            test.id,
            variant_a_impressions=1000,
            variant_a_clicks=50,
            variant_a_conversions=5,  # 0.5% conversion
            variant_b_impressions=1000,
            variant_b_clicks=60,
            variant_b_conversions=9,  # 0.9% conversion
        )

        assert updated.variant_a_ctr == 5.0  # 50/1000 * 100
        assert updated.variant_a_conversion_rate == 10.0  # 5/50 * 100
        assert updated.variant_b_conversion_rate == 15.0  # 9/60 * 100
        assert updated.winner == "B"  # Higher conversion rate

    @pytest.mark.asyncio
    async def test_list_active_tests(self, db: AsyncSession):
        """List active tests."""
        business_id = uuid4()
        svc = A_B_TestService(db)

        for i in range(3):
            await svc.create_test(
                business_id,
                uuid4(),
                f"Title A {i}",
                f"Title B {i}",
                f"Desc A {i}",
                f"Desc B {i}",
            )

        tests = await svc.list_tests(business_id)

        assert len(tests) == 3
        assert all(t.is_active for t in tests)
