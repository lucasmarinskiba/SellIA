"""
Test Suite: FOMO Star Player Implementation
Tests: campaigns, events, A/B testing, analytics
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.fomo.service import fomo_service
from app.domains.fomo.models import FOMOCampaign, FOMOEvent, FOMOABTest, FOMOMetric


@pytest.fixture
async def test_user_id():
    return uuid4()


@pytest.fixture
async def test_campaign(db: AsyncSession, test_user_id):
    campaign = await fomo_service.create_campaign(
        db,
        user_id=test_user_id,
        name="Test Scarcity Campaign",
        campaign_type="scarcity",
        headline="Only 5 left!",
        config={
            "stockThreshold": 5,
            "segment": "all",
            "messageTemplate": "template_1",
        },
    )
    await db.commit()
    return campaign


class TestCampaignManagement:
    async def test_create_campaign(self, db: AsyncSession, test_user_id):
        """Test campaign creation."""
        campaign = await fomo_service.create_campaign(
            db,
            user_id=test_user_id,
            name="Black Friday Sale",
            campaign_type="countdown",
            headline="48 hour sale",
            config={"countdownHours": 48},
        )
        await db.commit()

        assert campaign.name == "Black Friday Sale"
        assert campaign.status == "draft"
        assert campaign.user_id == test_user_id

    async def test_activate_campaign(self, db: AsyncSession, test_campaign):
        """Test campaign activation."""
        activated = await fomo_service.activate_campaign(db, test_campaign.id)
        await db.commit()

        assert activated.status == "active"
        assert activated.is_active is True

    async def test_get_campaigns(self, db: AsyncSession, test_user_id):
        """Test retrieving user campaigns."""
        c1 = await fomo_service.create_campaign(
            db,
            user_id=test_user_id,
            name="Campaign 1",
            campaign_type="scarcity",
            headline="H1",
            config={},
        )
        c2 = await fomo_service.create_campaign(
            db,
            user_id=test_user_id,
            name="Campaign 2",
            campaign_type="countdown",
            headline="H2",
            config={},
        )
        await db.commit()

        campaigns = await fomo_service.get_campaigns(db, test_user_id)
        assert len(campaigns) >= 2


class TestEventLogging:
    async def test_log_purchase_event(self, db: AsyncSession, test_campaign):
        """Test logging purchase events."""
        customer_id = uuid4()
        product_id = uuid4()

        event = await fomo_service.log_event(
            db,
            campaign_id=test_campaign.id,
            event_type="purchase",
            customer_id=customer_id,
            product_id=product_id,
            metadata={"revenue": 99.99, "customerName": "Juan"},
        )
        await db.commit()

        assert event.event_type == "purchase"
        assert event.customer_id == customer_id
        assert event.metadata["revenue"] == 99.99

    async def test_get_recent_events(self, db: AsyncSession, test_campaign):
        """Test retrieving recent events."""
        # Log 5 events
        for i in range(5):
            await fomo_service.log_event(
                db,
                campaign_id=test_campaign.id,
                event_type="view",
                metadata={"sequence": i},
            )
        await db.commit()

        events = await fomo_service.get_recent_events(db, test_campaign.id, limit=10)
        assert len(events) == 5

    async def test_get_event_count(self, db: AsyncSession, test_campaign):
        """Test event counting."""
        # Log purchase and view events
        await fomo_service.log_event(
            db, test_campaign.id, "purchase", metadata={"revenue": 50}
        )
        await fomo_service.log_event(
            db, test_campaign.id, "view", metadata={}
        )
        await fomo_service.log_event(
            db, test_campaign.id, "view", metadata={}
        )
        await db.commit()

        total = await fomo_service.get_event_count(db, test_campaign.id)
        purchases = await fomo_service.get_event_count(db, test_campaign.id, "purchase")

        assert total == 3
        assert purchases == 1


class TestABTesting:
    async def test_create_ab_test(self, db: AsyncSession, test_campaign):
        """Test A/B test creation."""
        variant_a = {"message": "Stock low", "color": "#ff0000"}
        variant_b = {"message": "Only 3 left!", "color": "#ef4444"}

        test = await fomo_service.create_ab_test(
            db, test_campaign.id, variant_a, variant_b
        )
        await db.commit()

        assert test.status == "running"
        assert test.variant_a_views == 0
        assert test.variant_b_views == 0

    async def test_ab_test_views(self, db: AsyncSession, test_campaign):
        """Test recording A/B test views."""
        test = await fomo_service.create_ab_test(
            db, test_campaign.id, {"msg": "A"}, {"msg": "B"}
        )
        await db.commit()

        # Record views
        await fomo_service.record_ab_test_view(db, test.id, "A")
        await fomo_service.record_ab_test_view(db, test.id, "A")
        await fomo_service.record_ab_test_view(db, test.id, "B")
        await db.commit()

        stats = await fomo_service.get_ab_test_stats(db, test.id)
        assert stats["variant_a"]["views"] == 2
        assert stats["variant_b"]["views"] == 1

    async def test_ab_test_conversions(self, db: AsyncSession, test_campaign):
        """Test recording A/B test conversions."""
        test = await fomo_service.create_ab_test(
            db, test_campaign.id, {"msg": "A"}, {"msg": "B"}
        )
        await db.commit()

        # Record views and conversions
        for _ in range(10):
            await fomo_service.record_ab_test_view(db, test.id, "A")
        for _ in range(3):
            await fomo_service.record_ab_test_conversion(db, test.id, "A")

        for _ in range(10):
            await fomo_service.record_ab_test_view(db, test.id, "B")
        for _ in range(2):
            await fomo_service.record_ab_test_conversion(db, test.id, "B")

        await db.commit()

        stats = await fomo_service.get_ab_test_stats(db, test.id)

        # A: 3/10 = 30%, B: 2/10 = 20%
        assert stats["variant_a"]["conversions"] == 3
        assert stats["variant_b"]["conversions"] == 2
        assert stats["variant_a"]["rate"] == pytest.approx(0.3)
        assert stats["variant_b"]["rate"] == pytest.approx(0.2)
        assert stats["winner"] == "A"  # 30% > 20% * 1.1


class TestMetricsAndAnalytics:
    async def test_record_impression_metric(self, db: AsyncSession, test_campaign):
        """Test recording impression metrics."""
        await fomo_service.record_metric(db, test_campaign.id, "impression")
        await fomo_service.record_metric(db, test_campaign.id, "impression")
        await db.commit()

        metrics = await fomo_service.get_metrics(db, test_campaign.id, days=1)
        assert len(metrics) == 1
        assert metrics[0]["impressions"] == 2

    async def test_record_conversion_metric(self, db: AsyncSession, test_campaign):
        """Test recording conversion metrics with revenue."""
        await fomo_service.record_metric(
            db, test_campaign.id, "impression"
        )
        await fomo_service.record_metric(
            db, test_campaign.id, "conversion", Decimal("99.99")
        )
        await fomo_service.record_metric(
            db, test_campaign.id, "conversion", Decimal("149.99")
        )
        await db.commit()

        metrics = await fomo_service.get_metrics(db, test_campaign.id, days=1)
        assert metrics[0]["conversions"] == 2
        assert float(metrics[0]["revenue"]) == pytest.approx(249.98)
        assert metrics[0]["conversion_rate"] == pytest.approx(66.67, rel=0.01)  # 2/3
        assert metrics[0]["aov"] == pytest.approx(124.99)

    async def test_get_summary_metrics(self, db: AsyncSession, test_campaign):
        """Test summary metrics calculation."""
        # Day 1
        await fomo_service.record_metric(
            db, test_campaign.id, "impression"
        )
        await fomo_service.record_metric(
            db, test_campaign.id, "impression"
        )
        await fomo_service.record_metric(
            db, test_campaign.id, "conversion", Decimal("100")
        )
        await db.commit()

        summary = await fomo_service.get_summary_metrics(db, test_campaign.id)
        assert summary["total_conversions"] == 1
        assert summary["total_revenue"] == 100.0
        assert summary["avg_conversion_rate"] == pytest.approx(50.0)  # 1/2
        assert summary["avg_aov"] == pytest.approx(100.0)

    async def test_metrics_time_window(self, db: AsyncSession, test_campaign):
        """Test metrics filtering by time window."""
        # Today
        await fomo_service.record_metric(db, test_campaign.id, "impression")
        await db.commit()

        metrics = await fomo_service.get_metrics(db, test_campaign.id, days=30)
        assert len(metrics) >= 1
        assert metrics[0]["impressions"] == 1


class TestIntegration:
    async def test_full_campaign_lifecycle(self, db: AsyncSession, test_user_id):
        """Test full campaign lifecycle: create → activate → log events → analytics."""
        # 1. Create campaign
        campaign = await fomo_service.create_campaign(
            db,
            user_id=test_user_id,
            name="Integration Test Campaign",
            campaign_type="scarcity",
            headline="Integration Test",
            config={},
        )
        await db.commit()

        # 2. Activate
        await fomo_service.activate_campaign(db, campaign.id)
        await db.commit()

        # 3. Log events
        customer_id = uuid4()
        for i in range(5):
            await fomo_service.log_event(
                db,
                campaign_id=campaign.id,
                event_type="view",
                customer_id=customer_id,
            )
        for i in range(2):
            await fomo_service.log_event(
                db,
                campaign_id=campaign.id,
                event_type="purchase",
                customer_id=customer_id,
                metadata={"revenue": 50 + i},
            )
        await db.commit()

        # 4. Record metrics
        await fomo_service.record_metric(db, campaign.id, "impression")
        await fomo_service.record_metric(db, campaign.id, "impression")
        await fomo_service.record_metric(db, campaign.id, "conversion", Decimal("150"))
        await db.commit()

        # 5. Verify analytics
        summary = await fomo_service.get_summary_metrics(db, campaign.id)
        assert summary["total_conversions"] == 1
        assert summary["total_revenue"] == 150.0

        campaigns = await fomo_service.get_campaigns(db, test_user_id)
        assert len(campaigns) >= 1
        assert campaigns[0].status == "active"
