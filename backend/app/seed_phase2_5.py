#!/usr/bin/env python3
"""Seed Phase 2-5 test data."""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from app.core.database import AsyncSessionLocal, engine, Base
from app.domains.businesses.models import Business, BusinessType, LocalizationModel
from app.domains.ml_pipelines.models import LeadScoringModel, ChurnPredictionModel, CLVModel
from app.domains.channel_routing.models import ChannelAffinityModel, MessageRouting, ChannelPerformanceMetrics
from app.domains.competitive_intelligence.models import CompetitorProfile, PriceOptimization, MarketAnalysis
from app.domains.performance_optimization.models import PerformanceMetrics

TEST_BUSINESS_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
TEST_USER_ID = uuid.UUID("a23e4567-e89b-12d3-a456-426614174000")
TEST_CUSTOMER_ID = uuid.UUID("223e4567-e89b-12d3-a456-426614174000")
TEST_PRODUCT_ID = uuid.UUID("323e4567-e89b-12d3-a456-426614174000")

async def seed():
    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Create Business first (required by FK)
        business = Business(
            id=TEST_BUSINESS_ID,
            user_id=TEST_USER_ID,
            name="Test Business",
            type=BusinessType.SERVICES,
            description="Test business for Phase 2-5 endpoints",
            localization_model=LocalizationModel.ONLINE_ONLY,
            is_active=True
        )
        db.add(business)
        await db.commit()
        # Phase 2: ML Pipelines
        lead = LeadScoringModel(
            business_id=TEST_BUSINESS_ID,
            lead_id=TEST_CUSTOMER_ID,
            lead_score=85.5,
            confidence=0.92,
            tier="hot",
            top_factors=["demo_attended", "email_engagement", "website_visits"]
        )
        db.add(lead)

        churn = ChurnPredictionModel(
            business_id=TEST_BUSINESS_ID,
            customer_id=TEST_CUSTOMER_ID,
            churn_probability=0.15,
            churn_risk="low",
            days_until_churn=180,
            recommended_action="maintain_engagement"
        )
        db.add(churn)

        clv = CLVModel(
            business_id=TEST_BUSINESS_ID,
            customer_id=TEST_CUSTOMER_ID,
            predicted_clv_12m=5000.0,
            predicted_clv_36m=15000.0,
            clv_segment="vip",
            upsell_propensity=0.75,
            crosssell_propensity=0.60
        )
        db.add(clv)

        # Phase 3: Channel Routing
        affinity = ChannelAffinityModel(
            business_id=TEST_BUSINESS_ID,
            customer_id=TEST_CUSTOMER_ID,
            email_score=0.85,
            sms_score=0.60,
            whatsapp_score=0.75,
            phone_score=0.40,
            push_score=0.55,
            in_app_score=0.70,
            recommended_primary="email",
            recommended_secondary="whatsapp"
        )
        db.add(affinity)

        perf = ChannelPerformanceMetrics(
            business_id=TEST_BUSINESS_ID,
            channel="email",
            total_messages_sent=10000,
            total_delivered=9800,
            total_opened=3200,
            total_clicked=800,
            total_responses=500,
            delivery_rate=0.98,
            open_rate=0.32
        )
        db.add(perf)

        # Phase 4: Competitive Intelligence (skip for now - model field mismatch)

        # Phase 5: Performance Optimization
        perf_metrics = PerformanceMetrics(
            business_id=TEST_BUSINESS_ID,
            total_requests=100000,
            total_errors=500,
            error_rate=0.005,
            avg_response_time_ms=150.0,
            p95_latency_ms=450.0,
            p99_latency_ms=950.0,
            requests_per_second=1000.0,
            db_avg_query_time_ms=25.0,
            cache_hit_rate=0.75,
            memory_usage_mb=512.0,
            cpu_usage_percent=45.0,
            performance_score=85
        )
        db.add(perf_metrics)

        await db.commit()
        print("✅ Test data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
