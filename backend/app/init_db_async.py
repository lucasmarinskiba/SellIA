#!/usr/bin/env python3
"""Initialize database async - Phase 2-5 + Phase 51."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import Base, engine
from app.domains.ml_pipelines.models import LeadScoringModel, ChurnPredictionModel, CLVModel
from app.domains.channel_routing.models import ChannelAffinityModel, MessageRouting, ChannelPerformanceMetrics
from app.domains.competitive_intelligence.models import CompetitorProfile, PriceOptimization, MarketAnalysis, CompetitiveIntelligenceFeed
from app.domains.performance_optimization.models import PerformanceMetrics, SlowQuery, IndexRecommendation, CacheStrategy, QueryOptimization
from app.domains.locations.models import LocationProfile, BusinessModel, ProximityEvent, OfflineConversion, LocationVisit
from app.domains.offline_analytics.models import OfflineToOnlineAttribution, OfflineAnalyticsMetrics, LocationFootTrafficHourly, PostVisitSequence, PostVisitSequenceExecution
from app.domains.channel_integration.models import GoogleBusinessProfileConnection, GoogleMapsLocation, LocationMessage, LocationMessageExecution, LocationReview
from app.domains.ai_content_generation.models import ContentTemplate, GeneratedContent, ContentPerformance, BulkContentGeneration, ContentVariant

async def init_db():
    """Create all tables."""
    print("Initializing database...")
    try:
        async with engine.begin() as conn:
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized successfully!")
        print("\nTables created:")
        print("Phase 2 (ML): LeadScoringModel, ChurnPredictionModel, CLVModel")
        print("Phase 3 (Channel): ChannelAffinityModel, MessageRouting, ChannelPerformanceMetrics")
        print("Phase 4 (Competitive): CompetitorProfile, PriceOptimization, MarketAnalysis, CompetitiveIntelligenceFeed")
        print("Phase 5 (Performance): PerformanceMetrics, SlowQuery, IndexRecommendation, CacheStrategy, QueryOptimization")
        print("Phase 5A (Locations): LocationProfile, BusinessModel, ProximityEvent, OfflineConversion, LocationVisit")
        print("Phase 5D (Analytics): OfflineToOnlineAttribution, OfflineAnalyticsMetrics, LocationFootTrafficHourly, PostVisitSequence, PostVisitSequenceExecution")
        print("Phase 5C (Integration): GoogleBusinessProfileConnection, GoogleMapsLocation, LocationMessage, LocationMessageExecution, LocationReview")
        print("Phase 51 (Content): ContentTemplate, GeneratedContent, ContentPerformance, BulkContentGeneration, ContentVariant")
        return True
    except Exception as e:
        print(f"❌ Database init failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(init_db())
    sys.exit(0 if success else 1)
