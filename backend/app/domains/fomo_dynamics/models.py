"""Phase X6: FOMO Dynamics - Ultra-Potent FOMO Engine."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base
import enum


class FOMOStrategy(str, enum.Enum):
    SCARCITY = "scarcity"  # Limited stock
    URGENCY = "urgency"  # Time-limited
    SOCIAL_PROOF = "social_proof"  # People buying now
    EXCLUSIVITY = "exclusivity"  # VIP/early access
    DYNAMIC_PRICING = "dynamic_pricing"  # Price rises with demand
    FLASH_SALE = "flash_sale"  # Surprise limited-time deal
    COUNTDOWN = "countdown"  # Timer pressure
    PERSONALIZED = "personalized"  # Behavior-based


class DynamicOffer(Base):
    __tablename__ = "dynamic_offers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Core offer data
    strategy = Column(Enum(FOMOStrategy), nullable=False)
    base_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)

    # Scarcity
    total_stock = Column(Integer, nullable=True)
    stock_taken = Column(Integer, default=0)
    stock_threshold_alert = Column(Integer, nullable=True)  # Alert when < N left

    # Urgency
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    time_limit_hours = Column(Integer, nullable=True)

    # Dynamic pricing
    price_multiplier = Column(Float, default=1.0)  # 1.0 = no change, 1.2 = 20% increase
    price_increase_per_purchase = Column(Float, default=0)  # +0.5 per unit sold

    # Social proof
    purchases_count = Column(Integer, default=0)
    viewers_count = Column(Integer, default=0)
    social_proof_message = Column(String(500), nullable=True)  # "{N} people bought this today"

    # Personalization
    target_user_segment = Column(String(100), nullable=True)  # VIP, new_users, frequent_buyers
    personalization_score = Column(Float, default=0)  # 0-1 how personalized for each user

    # Messaging
    headline = Column(String(200), nullable=False)  # "Grab yours before stock runs out!"
    description = Column(Text, nullable=True)
    urgency_badge = Column(String(50), nullable=True)  # "Only 5 left", "Ends in 2h", "Limited edition"
    cta_text = Column(String(100), default="Buy Now")

    # Tracking
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PriceElasticity(Base):
    __tablename__ = "price_elasticity"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Elasticity data
    elasticity_coefficient = Column(Float, default=-1.2)  # < -1 = elastic, > -1 = inelastic
    current_demand = Column(Integer, default=0)
    previous_price = Column(Float, nullable=True)
    previous_quantity = Column(Integer, nullable=True)
    optimal_price = Column(Float, nullable=True)

    # Tracking
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class FOMOBadge(Base):
    __tablename__ = "fomo_badges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_offers.id", ondelete="CASCADE"), nullable=False)

    # Badge data
    badge_type = Column(String(50), nullable=False)  # "stock_alert", "time_alert", "price_increase", "best_seller"
    urgency_level = Column(Integer, default=1)  # 1-5, 5 = most urgent
    badge_text = Column(String(100), nullable=False)
    badge_color = Column(String(20), default="red")  # red, orange, yellow
    badge_icon = Column(String(50), nullable=True)  # "fire", "clock", "trending"

    # Animation
    animate = Column(Boolean, default=True)
    animation_type = Column(String(50), nullable=True)  # "pulse", "blink", "shake"


class SocialProofReal(Base):
    __tablename__ = "social_proof_real"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Real activity
    recent_buyers = Column(JSONB, default=list)  # [{name, time_ago, profile_pic}]
    recent_views = Column(Integer, default=0)  # Views in last hour
    today_sales = Column(Integer, default=0)
    week_sales = Column(Integer, default=0)
    repeat_purchase_rate = Column(Float, default=0)  # % of repeat customers

    # Testimonials
    top_reviews = Column(JSONB, default=list)  # [{star_rating, text, buyer_name}]
    avg_rating = Column(Float, default=0)

    # Trust signals
    sales_velocity = Column(Integer, default=0)  # Units/hour
    is_bestseller = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class PersonalizedFOMO(Base):
    __tablename__ = "personalized_fomo"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # User behavior
    browse_count = Column(Integer, default=0)  # Times viewed product
    time_spent_seconds = Column(Integer, default=0)
    cart_abandoned = Column(Boolean, default=False)
    previously_purchased = Column(Boolean, default=False)

    # Personalization strategy
    trigger_message = Column(String(300), nullable=True)  # Custom message for this user
    trigger_type = Column(String(50), nullable=True)  # "price_drop", "back_in_stock", "friend_bought", "trending"
    persuasion_angle = Column(String(100), nullable=True)  # "scarcity", "urgency", "social_proof", "quality"

    # Effectiveness
    conversion_probability = Column(Float, default=0)  # 0-1 estimated chance they'll buy
    recommended_offer = Column(String(500), nullable=True)  # Best offer for this user

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
