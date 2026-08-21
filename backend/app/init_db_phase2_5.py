#!/usr/bin/env python3
"""Initialize database - Phase 2-5 only (no FK dependencies)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import Base, engine
from app.domains.ml_pipelines.models import LeadScoringModel, ChurnPredictionModel, CLVModel
from app.domains.channel_routing.models import ChannelAffinityModel, MessageRouting, ChannelPerformanceMetrics
from app.domains.competitive_intelligence.models import CompetitorProfile, PriceOptimization, MarketAnalysis, CompetitiveIntelligenceFeed
from app.domains.performance_optimization.models import PerformanceMetrics, SlowQuery, IndexRecommendation, CacheStrategy, QueryOptimization

async def init_phase2_5():
    """Create Phase 2-5 tables only."""
    print("Initializing Phase 2-5 database tables...")
    try:
        async with engine.begin() as conn:
            print("Creating Phase 2 (ML Pipelines) tables...")
            await conn.run_sync(LeadScoringModel.__table__.create, checkfirst=True)
            await conn.run_sync(ChurnPredictionModel.__table__.create, checkfirst=True)
            await conn.run_sync(CLVModel.__table__.create, checkfirst=True)
            print("✅ Phase 2 created")

            print("Creating Phase 3 (Channel Routing) tables...")
            await conn.run_sync(ChannelAffinityModel.__table__.create, checkfirst=True)
            await conn.run_sync(MessageRouting.__table__.create, checkfirst=True)
            await conn.run_sync(ChannelPerformanceMetrics.__table__.create, checkfirst=True)
            print("✅ Phase 3 created")

            print("Creating Phase 4 (Competitive Intelligence) tables...")
            await conn.run_sync(CompetitorProfile.__table__.create, checkfirst=True)
            await conn.run_sync(PriceOptimization.__table__.create, checkfirst=True)
            await conn.run_sync(MarketAnalysis.__table__.create, checkfirst=True)
            await conn.run_sync(CompetitiveIntelligenceFeed.__table__.create, checkfirst=True)
            print("✅ Phase 4 created")

            print("Creating Phase 5 (Performance Optimization) tables...")
            await conn.run_sync(PerformanceMetrics.__table__.create, checkfirst=True)
            await conn.run_sync(SlowQuery.__table__.create, checkfirst=True)
            await conn.run_sync(IndexRecommendation.__table__.create, checkfirst=True)
            await conn.run_sync(CacheStrategy.__table__.create, checkfirst=True)
            await conn.run_sync(QueryOptimization.__table__.create, checkfirst=True)
            print("✅ Phase 5 created")

        print("\n✅ All Phase 2-5 tables initialized successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(init_phase2_5())
    sys.exit(0 if success else 1)
