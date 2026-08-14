"""Phase 3 Database Models - Authority Building (E-E-A-T Signals)."""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

from backend.app.database import Base


class Testimonial(Base):
    """Customer testimonials + video reviews."""
    __tablename__ = "testimonials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_avatar = Column(String(500), nullable=True)
    title = Column(String(255), nullable=False)  # Quote headline
    content = Column(Text, nullable=False)
    video_url = Column(String(500), nullable=True)  # Loom, YouTube embed
    rating = Column(Integer, default=5)  # 1-5 stars
    industry = Column(String(255), nullable=True)  # Customer industry
    company = Column(String(255), nullable=True)  # Customer company
    metrics = Column(Text, nullable=True)  # "Increased sales by 40%", JSON
    is_verified = Column(Boolean, default=False)  # Verified purchase/review
    is_featured = Column(Boolean, default=False)  # Pinned on homepage
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_testimonials', 'seller_id', 'is_verified'),
        Index('idx_featured', 'seller_id', 'is_featured'),
    )


class Award(Base):
    """Awards, certifications, badges."""
    __tablename__ = "awards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)  # "Best Seller 2024", "Industry Leader"
    issuer = Column(String(255), nullable=False)  # Platform/org that issued (ML, Amazon, TrustPilot)
    category = Column(String(50), nullable=False)  # bestseller, top_rated, certified, award
    badge_url = Column(String(500), nullable=True)  # Badge image
    certificate_url = Column(String(500), nullable=True)  # PDF certificate
    awarded_date = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)  # Expiry date
    verification_url = Column(String(500), nullable=True)  # Link to verify badge
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_awards', 'seller_id', 'is_active'),
        Index('idx_category', 'category', 'awarded_date'),
    )


class Review(Base):
    """Aggregated reviews from all platforms (unified view)."""
    __tablename__ = "platform_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # mercado_libre, amazon, hotmart, trustpilot
    platform_review_id = Column(String(255), nullable=True)
    reviewer_name = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text, nullable=False)
    review_date = Column(DateTime, nullable=False)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)  # Upvotes
    seller_response = Column(Text, nullable=True)
    response_date = Column(DateTime, nullable=True)
    is_flagged = Column(Boolean, default=False)  # Spam/abuse
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_reviews', 'seller_id', 'rating'),
        Index('idx_platform_reviews', 'platform', 'review_date'),
    )


class TrustScore(Base):
    """Overall trust/authority score (calculated daily)."""
    __tablename__ = "trust_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False)
    score_date = Column(DateTime, default=datetime.utcnow)

    # Component scores (0-100 each)
    review_rating_score = Column(Float, default=0)  # Avg review rating
    review_count_score = Column(Float, default=0)  # Number of reviews
    response_rate_score = Column(Float, default=0)  # % seller responses
    verification_score = Column(Float, default=0)  # Verified badges/certs
    longevity_score = Column(Float, default=0)  # Years selling

    # Overall
    trust_score = Column(Float, default=0)  # Weighted average (0-100)
    rank_tier = Column(String(50), default="bronze")  # bronze, silver, gold, platinum

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_trust_seller', 'seller_id', 'score_date'),
    )


class SellerBio(Base):
    """Seller biography + expertise (E-E-A-T signals)."""
    __tablename__ = "seller_bios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String(255), nullable=False, unique=True)

    # Expertise
    full_name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=False)  # "15+ years in e-commerce"
    years_in_business = Column(Integer, nullable=False)
    specialties = Column(ARRAY(String), nullable=True)  # ["electronics", "refurbished"]

    # Authoritativeness
    linkedin_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    media_appearances = Column(ARRAY(String), nullable=True)  # Articles, podcasts

    # Trust
    avatar_url = Column(String(500), nullable=True)
    certification_text = Column(Text, nullable=True)  # "Certified [XYZ]"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_seller_bio', 'seller_id'),
    )
