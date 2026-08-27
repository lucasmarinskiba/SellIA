"""
FOMO Star Player: Demo Seed Data
Quickly populate database with example campaigns for testing
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.domains.fomo.models import FOMOCampaign, FOMOEvent, FOMOMetric
from app.domains.fomo.service import fomo_service


async def seed_demo_data():
    """Seed database with demo FOMO campaigns & data."""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as db:
        print("🌱 Seeding FOMO demo data...")

        # Get or create demo user
        demo_user_id = uuid4()
        print(f"  Demo User ID: {demo_user_id}")

        # Campaign 1: Scarcity (High-performing)
        print("\n  📦 Campaign 1: Stock Scarcity")
        campaign1 = await fomo_service.create_campaign(
            db,
            user_id=demo_user_id,
            name="Stock Running Low - Premium Plan",
            campaign_type="scarcity",
            headline="Only 3 Premium Seats Left!",
            config={
                "stockThreshold": 5,
                "segment": "all",
                "messageTemplate": "template_stock_low",
            },
        )
        await fomo_service.activate_campaign(db, campaign1.id)
        await db.commit()

        # Log events for campaign 1 (high conversion)
        for i in range(100):
            await fomo_service.log_event(
                db,
                campaign_id=campaign1.id,
                event_type="view",
                customer_id=uuid4(),
            )
            if i % 12 == 0:  # ~8% conversion
                await fomo_service.log_event(
                    db,
                    campaign_id=campaign1.id,
                    event_type="purchase",
                    customer_id=uuid4(),
                    metadata={"revenue": Decimal("199.99"), "customerName": f"Customer_{i}"},
                )
        await db.commit()

        # Record metrics for campaign 1
        for day in range(-30, 1):
            date = (datetime.now(timezone.utc).date() + timedelta(days=day))
            await fomo_service.record_metric(db, campaign1.id, "impression")
            await fomo_service.record_metric(
                db, campaign1.id, "conversion", Decimal("199.99")
            )
        await db.commit()
        print(f"    ✓ Created: {campaign1.name}")

        # Campaign 2: Countdown (Medium-performing)
        print("\n  ⏰ Campaign 2: Limited Time Offer")
        campaign2 = await fomo_service.create_campaign(
            db,
            user_id=demo_user_id,
            name="Flash Sale - 48 Hour Window",
            campaign_type="countdown",
            headline="50% OFF - Ends in 48 Hours",
            config={
                "countdownHours": 48,
                "discountPercent": 50,
                "segment": "all",
            },
        )
        await fomo_service.activate_campaign(db, campaign2.id)
        await db.commit()

        # Log events for campaign 2
        for i in range(150):
            await fomo_service.log_event(
                db,
                campaign_id=campaign2.id,
                event_type="view",
                customer_id=uuid4(),
            )
            if i % 15 == 0:  # ~6.7% conversion
                await fomo_service.log_event(
                    db,
                    campaign_id=campaign2.id,
                    event_type="purchase",
                    customer_id=uuid4(),
                    metadata={"revenue": Decimal("99.99"), "customerName": f"Buyer_{i}"},
                )
        await db.commit()
        print(f"    ✓ Created: {campaign2.name}")

        # Campaign 3: Social Proof (Testing)
        print("\n  👥 Campaign 3: Social Proof Feed")
        campaign3 = await fomo_service.create_campaign(
            db,
            user_id=demo_user_id,
            name="Real-time Activity Stream",
            campaign_type="social_proof",
            headline="See what others are buying",
            config={"segment": "all"},
        )
        await fomo_service.activate_campaign(db, campaign3.id)
        await db.commit()

        # Log recent activity
        for i in range(20):
            await fomo_service.log_event(
                db,
                campaign_id=campaign3.id,
                event_type="purchase",
                customer_id=uuid4(),
                metadata={
                    "customerName": f"Customer {chr(65 + (i % 26))}",
                    "productName": f"Product #{i % 5 + 1}",
                },
            )
        await db.commit()
        print(f"    ✓ Created: {campaign3.name}")

        # Campaign 4: A/B Testing (Setup for testing)
        print("\n  🧪 Campaign 4: A/B Test Example")
        campaign4 = await fomo_service.create_campaign(
            db,
            user_id=demo_user_id,
            name="Copywriting A/B Test",
            campaign_type="scarcity",
            headline="Testing message variants",
            config={},
        )
        await fomo_service.activate_campaign(db, campaign4.id)

        # Create A/B test
        test = await fomo_service.create_ab_test(
            db,
            campaign_id=campaign4.id,
            variant_a={"message": "Stock low", "color": "#ff0000"},
            variant_b={"message": "Only 3 left!", "color": "#ef4444"},
        )
        await db.commit()

        # Simulate A/B test traffic (variant A performing better)
        for i in range(100):
            await fomo_service.record_ab_test_view(db, test.id, "A")
            if i % 8 == 0:  # 12.5% CR
                await fomo_service.record_ab_test_conversion(db, test.id, "A")

        for i in range(100):
            await fomo_service.record_ab_test_view(db, test.id, "B")
            if i % 10 == 0:  # 10% CR
                await fomo_service.record_ab_test_conversion(db, test.id, "B")

        await db.commit()
        print(f"    ✓ Created: {campaign4.name} + A/B test")

        # Summary
        print("\n✅ Seed complete!")
        print(f"  Created 4 campaigns for user: {demo_user_id}")
        print(f"  Campaign IDs:")
        print(f"    1. Scarcity: {campaign1.id}")
        print(f"    2. Countdown: {campaign2.id}")
        print(f"    3. Social Proof: {campaign3.id}")
        print(f"    4. A/B Test: {campaign4.id}")

        # Show analytics preview
        print("\n📊 Analytics Preview:")
        for campaign in [campaign1, campaign2, campaign3]:
            summary = await fomo_service.get_summary_metrics(db, campaign.id)
            print(f"\n  {campaign.name}:")
            print(f"    Conversions: {summary['total_conversions']}")
            print(f"    Revenue: ${summary['total_revenue']:.2f}")
            print(f"    CR: {summary['avg_conversion_rate']:.2f}%")
            print(f"    AOV: ${summary['avg_aov']:.2f}")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
