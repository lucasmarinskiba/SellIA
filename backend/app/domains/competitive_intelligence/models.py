"""Phase 4: Competitive Intelligence - Market Analysis & Price Optimization."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class CompetitorProfile(Base):
    __tablename__ = "competitor_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    competitor_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False)

    # Market positioning
    market_segment = Column(String(100), nullable=True)  # "enterprise", "mid-market", "SMB", "startup"
    estimated_market_share = Column(Float, default=0)  # 0-1
    price_point = Column(Float, nullable=True)  # avg competitor price

    # Competitive analysis
    strength_areas = Column(JSONB, default=list)  # ["AI", "pricing", "UX", "support"]
    weakness_areas = Column(JSONB, default=list)  # ["enterprise security", "integrations"]
    differentiation_factors = Column(JSONB, default=list)  # unique selling points

    # Intelligence
    feature_set = Column(JSONB, default=list)  # ["automation", "analytics", "CRM", ...]
    customer_base_size = Column(Integer, default=0)  # estimated
    estimated_revenue_usd = Column(Float, default=0)
    funding_status = Column(String(50), nullable=True)  # "bootstrapped", "VC-funded", "profitable"

    # Threat assessment (0-100)
    competitive_threat_score = Column(Integer, default=50)  # 0=no threat, 100=high threat
    feature_parity_gap = Column(Float, default=0)  # 0-1, how far behind on features
    price_competitiveness = Column(Float, default=0.5)  # 0-1, lower=more aggressive pricing

    # Data freshness
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    data_source = Column(String(50), default="manual")  # "manual", "web_scrape", "api", "survey"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class PriceOptimization(Base):
    __tablename__ = "price_optimizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=True)

    # Pricing data
    current_price = Column(Float, nullable=False)
    competitor_avg_price = Column(Float, nullable=True)
    competitor_min_price = Column(Float, nullable=True)
    competitor_max_price = Column(Float, nullable=True)

    # Optimization
    suggested_price = Column(Float, nullable=False)
    price_elasticity = Column(Float, default=0)  # -2 to 0, demand sensitivity
    confidence_score = Column(Float, default=0)  # 0-1

    # Reasoning & factors
    optimization_strategy = Column(String(50), default="competitive")  # "competitive", "premium", "value", "penetration"
    key_factors = Column(JSONB, default=list)  # ["market_share_gain", "revenue_max", "churn_reduction"]
    reasoning = Column(Text, nullable=True)  # explain the recommendation

    # Expected impact
    estimated_demand_impact = Column(Float, default=0)  # -0.5 to +0.5, % change expected
    estimated_revenue_impact = Column(Float, default=0)  # % change in revenue
    estimated_margin_impact = Column(Float, default=0)  # % change in margin

    # Tracking
    is_implemented = Column(Boolean, default=False)
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    actual_performance = Column(JSONB, nullable=True)  # track real results

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class MarketAnalysis(Base):
    __tablename__ = "market_analyses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    market_segment = Column(String(100), nullable=False, index=True)  # "enterprise", "mid-market", "SMB"

    # Market snapshot
    total_addressable_market_usd = Column(Float, default=0)  # TAM
    serviceable_market_usd = Column(Float, default=0)  # SAM
    serviceable_obtainable_market_usd = Column(Float, default=0)  # SOM

    # Competitive landscape
    num_competitors = Column(Integer, default=0)
    market_leader = Column(String(255), nullable=True)
    leader_market_share = Column(Float, default=0)  # 0-1
    avg_price_point = Column(Float, default=0)

    # Business position
    your_current_market_share = Column(Float, default=0)  # 0-1
    positioning_score = Column(Integer, default=50)  # 0-100, how well positioned
    competitive_intensity = Column(Integer, default=50)  # 0-100, how crowded
    market_growth_rate = Column(Float, default=0)  # YoY % growth

    # Opportunities & threats
    opportunities = Column(JSONB, default=list)  # ["emerging_segment", "price_gap", "feature_gap"]
    threats = Column(JSONB, default=list)  # ["new_entrant", "price_war", "consolidation"]
    recommended_actions = Column(JSONB, default=list)  # ["expand_segment", "premium_positioning"]

    # Forward-looking
    market_outlook = Column(String(20), default="stable")  # "declining", "stable", "growing", "explosive"
    forecast_12m_share = Column(Float, default=0)  # predicted market share in 12m

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class CompetitiveIntelligenceFeed(Base):
    __tablename__ = "competitive_intel_feeds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Feed metadata
    feed_type = Column(String(50), nullable=False)  # "pricing_change", "feature_launch", "funding", "partnership", "news"
    competitor_name = Column(String(255), nullable=False)

    # Event details
    event_title = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=True)

    # Impact assessment
    relevance_score = Column(Float, default=0)  # 0-1, how relevant to your business
    threat_level = Column(String(20), default="low")  # "low", "medium", "high", "critical"
    recommended_response = Column(String(255), nullable=True)

    # Source
    source_url = Column(String(500), nullable=True)
    source_type = Column(String(50), default="unknown")  # "news", "social", "website", "api"

    # Status
    is_acknowledged = Column(Boolean, default=False)
    action_taken = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
