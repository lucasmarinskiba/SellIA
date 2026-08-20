"""Phase 4: Competitive Intelligence Service - Market Analysis & Price Optimization."""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domains.competitive_intelligence.models import (
    CompetitorProfile,
    PriceOptimization,
    MarketAnalysis,
    CompetitiveIntelligenceFeed,
)


class CompetitiveIntelligenceService:
    @staticmethod
    async def track_competitor(
        db: AsyncSession,
        business_id: UUID,
        competitor_name: str,
        industry: str,
        market_segment: str = None,
        price_point: float = None,
        strength_areas: List[str] = None,
        weakness_areas: List[str] = None,
        feature_set: List[str] = None,
    ) -> dict:
        """Register/update competitor profile."""
        result = await db.execute(
            select(CompetitorProfile).where(
                (CompetitorProfile.business_id == business_id)
                & (CompetitorProfile.competitor_name == competitor_name)
            )
        )
        competitor = result.scalar()

        if not competitor:
            competitor = CompetitorProfile(
                business_id=business_id,
                competitor_name=competitor_name,
                industry=industry,
            )
            db.add(competitor)

        competitor.market_segment = market_segment
        competitor.price_point = price_point
        competitor.strength_areas = strength_areas or []
        competitor.weakness_areas = weakness_areas or []
        competitor.feature_set = feature_set or []
        competitor.last_analyzed_at = datetime.now(timezone.utc)

        # Simple threat scoring: pricing aggression + feature count
        threat_score = 50
        if price_point and price_point < 100:
            threat_score += 20  # aggressive pricing
        if feature_set and len(feature_set) > 10:
            threat_score += 15  # feature-rich
        competitor.competitive_threat_score = min(threat_score, 100)

        await db.commit()
        await db.refresh(competitor)

        return {
            "competitor_id": competitor.id,
            "competitor_name": competitor.competitor_name,
            "threat_score": competitor.competitive_threat_score,
            "strengths": competitor.strength_areas,
            "weaknesses": competitor.weakness_areas,
        }

    @staticmethod
    async def analyze_price_positioning(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        current_price: float,
        competitor_prices: List[float] = None,
        target_margin: float = 0.4,
        market_position: str = "competitive",
    ) -> dict:
        """Recommend optimal price based on market analysis."""
        # Get competitor avg price
        if competitor_prices:
            competitor_avg = sum(competitor_prices) / len(competitor_prices)
            competitor_min = min(competitor_prices)
            competitor_max = max(competitor_prices)
        else:
            competitor_avg = current_price
            competitor_min = current_price * 0.9
            competitor_max = current_price * 1.1

        # Price optimization logic
        if market_position == "premium":
            suggested_price = competitor_max * 1.15
            strategy = "premium"
            elasticity = -1.5  # premium: less price sensitive
        elif market_position == "value":
            suggested_price = competitor_min * 0.95
            strategy = "penetration"
            elasticity = -2.0  # price sensitive
        else:  # competitive
            suggested_price = competitor_avg
            strategy = "competitive"
            elasticity = -1.2

        # Confidence based on data quantity & stability
        confidence = 0.7 if competitor_prices else 0.5

        # Impact estimation
        price_change_pct = (suggested_price - current_price) / current_price if current_price > 0 else 0
        estimated_demand_impact = elasticity * price_change_pct
        estimated_revenue_impact = price_change_pct + estimated_demand_impact
        estimated_margin_impact = price_change_pct  # margin improves as price goes up (assuming fixed costs)

        # Store optimization record
        optimization = PriceOptimization(
            business_id=business_id,
            product_id=product_id,
            current_price=current_price,
            competitor_avg_price=competitor_avg,
            competitor_min_price=competitor_min,
            competitor_max_price=competitor_max,
            suggested_price=suggested_price,
            price_elasticity=elasticity,
            confidence_score=confidence,
            optimization_strategy=strategy,
            key_factors=["market_share_gain", "revenue_max"],
            estimated_demand_impact=estimated_demand_impact,
            estimated_revenue_impact=estimated_revenue_impact,
            estimated_margin_impact=estimated_margin_impact,
        )
        db.add(optimization)
        await db.commit()
        await db.refresh(optimization)

        return {
            "product_id": product_id,
            "current_price": current_price,
            "competitor_avg": round(competitor_avg, 2),
            "suggested_price": round(suggested_price, 2),
            "strategy": strategy,
            "confidence": round(confidence, 2),
            "estimated_demand_impact": round(estimated_demand_impact * 100, 1),
            "estimated_revenue_impact": round(estimated_revenue_impact * 100, 1),
            "estimated_margin_impact": round(estimated_margin_impact * 100, 1),
        }

    @staticmethod
    async def get_competitive_landscape(
        db: AsyncSession,
        business_id: UUID,
        market_segment: str = None,
    ) -> dict:
        """Analyze competitive landscape for market segment."""
        # Get all competitors for business
        result = await db.execute(
            select(CompetitorProfile).where(
                CompetitorProfile.business_id == business_id
            )
        )
        competitors = result.scalars().all()

        if market_segment:
            competitors = [c for c in competitors if c.market_segment == market_segment]

        if not competitors:
            return {
                "market_segment": market_segment,
                "status": "no_data",
                "message": "No competitors tracked yet",
            }

        # Calculate market metrics
        avg_price = sum([c.price_point for c in competitors if c.price_point]) / len(
            [c for c in competitors if c.price_point]
        ) if any(c.price_point for c in competitors) else 0

        avg_threat = sum([c.competitive_threat_score for c in competitors]) / len(competitors)

        return {
            "market_segment": market_segment or "all",
            "num_competitors": len(competitors),
            "avg_price": round(avg_price, 2),
            "avg_threat_score": round(avg_threat, 0),
            "leaders": [
                {
                    "name": c.competitor_name,
                    "threat_score": c.competitive_threat_score,
                    "price": c.price_point,
                    "strengths": c.strength_areas[:3],
                }
                for c in sorted(competitors, key=lambda x: x.competitive_threat_score, reverse=True)[:3]
            ],
        }

    @staticmethod
    async def identify_market_opportunities(
        db: AsyncSession,
        business_id: UUID,
    ) -> dict:
        """Identify gaps and opportunities in market."""
        # Get all analysis records
        result = await db.execute(
            select(MarketAnalysis).where(
                MarketAnalysis.business_id == business_id
            )
        )
        analyses = result.scalars().all()

        opportunities = []
        threats = []

        for analysis in analyses:
            if analysis.positioning_score < 40:
                opportunities.append(f"Poor positioning in {analysis.market_segment}: consider differentiation")

            if analysis.competitive_intensity > 70:
                threats.append(f"High competition in {analysis.market_segment}: consider niche focus")

            if analysis.market_growth_rate > 0.2:
                opportunities.append(f"Fast-growing market: {analysis.market_segment} - expand aggressively")

            if analysis.your_current_market_share < 0.05 and analysis.num_competitors > 10:
                opportunities.append(f"Consolidation opportunity: {analysis.market_segment} is fragmented")

        return {
            "business_id": business_id,
            "opportunities": opportunities[:5],
            "threats": threats[:5],
            "top_priority": opportunities[0] if opportunities else "Monitor competitive landscape",
        }

    @staticmethod
    async def add_intelligence_feed(
        db: AsyncSession,
        business_id: UUID,
        feed_type: str,
        competitor_name: str,
        event_title: str,
        event_description: str = None,
        threat_level: str = "medium",
        source_url: str = None,
    ) -> dict:
        """Log competitive intelligence event."""
        feed = CompetitiveIntelligenceFeed(
            business_id=business_id,
            feed_type=feed_type,
            competitor_name=competitor_name,
            event_title=event_title,
            event_description=event_description,
            threat_level=threat_level,
            source_url=source_url,
        )

        # Auto-suggest response based on threat
        if threat_level == "critical":
            feed.recommended_response = "Immediate executive review and response strategy"
        elif threat_level == "high":
            feed.recommended_response = "Competitive analysis and counter-strategy within 48h"
        elif threat_level == "medium":
            feed.recommended_response = "Monitor and assess impact on pricing/positioning"

        # Relevance scoring
        if feed_type in ["pricing_change", "feature_launch"]:
            feed.relevance_score = 0.9
        elif feed_type in ["funding", "partnership"]:
            feed.relevance_score = 0.7
        else:
            feed.relevance_score = 0.5

        db.add(feed)
        await db.commit()
        await db.refresh(feed)

        return {
            "feed_id": feed.id,
            "competitor": competitor_name,
            "type": feed_type,
            "threat_level": threat_level,
            "recommended_action": feed.recommended_response,
        }

    @staticmethod
    async def get_intelligence_dashboard(
        db: AsyncSession,
        business_id: UUID,
    ) -> dict:
        """Get comprehensive competitive intelligence dashboard."""
        # Get recent feeds
        result = await db.execute(
            select(CompetitiveIntelligenceFeed)
            .where(CompetitiveIntelligenceFeed.business_id == business_id)
            .order_by(CompetitiveIntelligenceFeed.created_at.desc())
            .limit(10)
        )
        recent_feeds = result.scalars().all()

        # Get unacknowledged critical items
        critical_count = await db.execute(
            select(func.count(CompetitiveIntelligenceFeed.id)).where(
                (CompetitiveIntelligenceFeed.business_id == business_id)
                & (CompetitiveIntelligenceFeed.threat_level == "critical")
                & (~CompetitiveIntelligenceFeed.is_acknowledged)
            )
        )
        critical_items = critical_count.scalar() or 0

        # Get price optimizations awaiting implementation
        impl_result = await db.execute(
            select(PriceOptimization).where(
                (PriceOptimization.business_id == business_id)
                & (~PriceOptimization.is_implemented)
            )
        )
        pending_optimizations = result.scalars().all()

        return {
            "business_id": business_id,
            "critical_alerts": critical_items,
            "recent_intelligence": [
                {
                    "competitor": f.competitor_name,
                    "type": f.feed_type,
                    "title": f.event_title,
                    "threat_level": f.threat_level,
                    "date": f.event_date.isoformat() if f.event_date else f.created_at.isoformat(),
                }
                for f in recent_feeds[:5]
            ],
            "pending_price_optimizations": len(pending_optimizations),
            "recommendation": "Review critical alerts and implement recommended price optimizations" if critical_items > 0 else "Market stable - monitor for changes",
        }
