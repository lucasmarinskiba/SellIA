"""Phase 47: SEO & Marketplace Positioning Engine."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class KeywordResearch(Base):
    __tablename__ = "keyword_research"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, default=0)
    difficulty = Column(Integer, default=0)  # 0-100
    cpc = Column(Float, default=0)
    competition_level = Column(String(50), nullable=False)  # low, medium, high
    intent = Column(String(50), nullable=False)  # commercial, informational, navigational
    trend = Column(String(50), nullable=False)  # rising, stable, declining
    ranking_position = Column(Integer, nullable=True)
    platform = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ProductListing(Base):
    __tablename__ = "product_listings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    listing_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    bullet_points = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    search_ranking = Column(Integer, nullable=True)
    visibility_score = Column(Float, default=0)
    optimization_score = Column(Float, default=0)
    views_last_30d = Column(Integer, default=0)
    conversions_last_30d = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class RankingTracker(Base):
    __tablename__ = "ranking_tracker"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    current_rank = Column(Integer, default=0)
    previous_rank = Column(Integer, default=0)
    rank_change = Column(Integer, default=0)
    organic_impressions = Column(Integer, default=0)
    organic_clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0)
    tracked_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SEOOptimization(Base):
    __tablename__ = "seo_optimization"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    title_optimized = Column(Boolean, default=False)
    description_optimized = Column(Boolean, default=False)
    keywords_optimized = Column(Boolean, default=False)
    images_optimized = Column(Boolean, default=False)
    price_competitive = Column(Boolean, default=False)
    rating_score = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    overall_score = Column(Float, default=0)
    recommendations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class WebPagePerformance(Base):
    __tablename__ = "web_page_performance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    page_url = Column(String(500), nullable=False)
    page_title = Column(String(255), nullable=False)
    page_type = Column(String(50), nullable=False)  # product, category, blog, homepage
    organic_traffic = Column(Integer, default=0)
    organic_revenue = Column(Float, default=0)
    ranking_keywords = Column(Integer, default=0)
    top_10_keywords = Column(Integer, default=0)
    page_speed = Column(Float, default=0)
    mobile_score = Column(Float, default=0)
    core_web_vitals = Column(JSONB, nullable=True)
    tracked_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
