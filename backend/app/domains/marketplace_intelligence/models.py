"""Phase 48: Marketplace Intelligence & Competitive Analysis."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class CompetitorTracking(Base):
    __tablename__ = "competitor_tracking"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    competitor_url = Column(String(500), nullable=True)
    platform = Column(String(50), nullable=False)
    competitor_price = Column(Float, default=0)
    competitor_rating = Column(Float, default=0)
    competitor_reviews = Column(Integer, default=0)
    our_price = Column(Float, default=0)
    price_difference = Column(Float, default=0)
    price_difference_percent = Column(Float, default=0)
    stock_available = Column(Boolean, default=True)
    tracked_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class MarketAnalysis(Base):
    __tablename__ = "market_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    total_sellers = Column(Integer, default=0)
    total_listings = Column(Integer, default=0)
    average_price = Column(Float, default=0)
    price_range = Column(JSONB, nullable=True)
    average_rating = Column(Float, default=0)
    demand_level = Column(String(50), nullable=False)  # high, medium, low
    supply_level = Column(String(50), nullable=False)
    trend = Column(String(50), nullable=False)  # rising, stable, declining
    market_size = Column(Float, default=0)
    market_growth = Column(Float, default=0)
    analyzed_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class PriceOptimization(Base):
    __tablename__ = "price_optimization"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    current_price = Column(Float, default=0)
    recommended_price = Column(Float, default=0)
    price_elasticity = Column(Float, default=0)
    demand_curve = Column(JSONB, nullable=True)
    optimal_margin = Column(Float, default=0)
    competitor_avg_price = Column(Float, default=0)
    price_position = Column(String(50), nullable=False)  # premium, competitive, value
    revenue_impact = Column(Float, default=0)
    profit_impact = Column(Float, default=0)
    optimization_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ProductResearch(Base):
    __tablename__ = "product_research"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    category = Column(String(255), nullable=False)
    product_name = Column(String(500), nullable=False)
    estimated_demand = Column(Integer, default=0)
    estimated_supply = Column(Integer, default=0)
    potential_revenue = Column(Float, default=0)
    competition_level = Column(String(50), nullable=False)
    profit_potential = Column(Float, default=0)
    trend_score = Column(Float, default=0)
    recommendation = Column(String(50), nullable=False)  # pursue, research, avoid
    research_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SeasonalTrends(Base):
    __tablename__ = "seasonal_trends"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    month = Column(String(50), nullable=False)
    expected_demand = Column(Integer, default=0)
    expected_price = Column(Float, default=0)
    expected_revenue = Column(Float, default=0)
    actual_demand = Column(Integer, nullable=True)
    actual_price = Column(Float, nullable=True)
    actual_revenue = Column(Float, nullable=True)
    accuracy = Column(Float, default=0)
