"""Phase X7: Perception Engineering Agent - Psychology-Driven Perception Shift."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base
import enum


class PerceptionDimension(str, enum.Enum):
    QUALITY = "quality"  # Premium vs cheap
    VALUE = "value"  # Worth vs overpriced
    TRUST = "trust"  # Reliable vs risky
    EXCLUSIVITY = "exclusivity"  # Unique vs commodity
    INNOVATION = "innovation"  # Cutting-edge vs outdated
    EMOTIONAL = "emotional"  # Desirable vs indifferent
    AUTHORITY = "authority"  # Expert vs unknown
    BELONGING = "belonging"  # In-group vs outsider


class PerceptionShiftTechnique(str, enum.Enum):
    ANCHORING = "anchoring"  # Reference point (compare to expensive = cheap)
    REFRAMING = "reframing"  # Same fact, different angle
    STORYTELLING = "storytelling"  # Narrative changes perception
    SOCIAL_PROOF = "social_proof"  # Others think X = you should too
    AUTHORITY = "authority"  # Expert endorsement
    CONTRAST = "contrast"  # Compare to worse alternative
    BUNDLING = "bundling"  # Add value perception
    LOSS_AVERSION = "loss_aversion"  # Risk of missing out
    RECIPROCITY = "reciprocity"  # Feeling of obligation


class ProductPerception(Base):
    __tablename__ = "product_perceptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Current perception (0-10 scale)
    quality_score = Column(Float, default=5.0)  # How premium/high-quality perceived
    value_score = Column(Float, default=5.0)  # Worth the money
    trust_score = Column(Float, default=5.0)  # Reliability & safety
    exclusivity_score = Column(Float, default=5.0)  # Uniqueness & rarity
    innovation_score = Column(Float, default=5.0)  # Modern & cutting-edge
    emotional_score = Column(Float, default=5.0)  # Desirability & attraction
    authority_score = Column(Float, default=5.0)  # Expert-backed
    belonging_score = Column(Float, default=5.0)  # In-group status

    # Target perception (goals)
    target_quality = Column(Float, default=8.0)
    target_value = Column(Float, default=8.0)
    target_trust = Column(Float, default=9.0)
    target_exclusivity = Column(Float, default=7.0)

    # Actual product facts
    actual_quality = Column(Text, nullable=True)  # Real specs
    actual_value = Column(Text, nullable=True)  # Real ROI/benefit
    actual_unique_features = Column(JSONB, default=list)  # Real differentiators

    # Customer segment perception
    target_segment = Column(String(100), nullable=True)  # "luxury_buyers", "budget", "professionals"
    segment_perception_gap = Column(Float, default=0)  # Difference: target - current

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PerceptionShiftCampaign(Base):
    __tablename__ = "perception_shift_campaigns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Campaign strategy
    target_dimension = Column(Enum(PerceptionDimension), nullable=False)
    technique = Column(Enum(PerceptionShiftTechnique), nullable=False)
    perception_score_before = Column(Float)
    perception_score_target = Column(Float)

    # Messaging strategy
    headline = Column(String(200), nullable=False)
    subheadline = Column(String(300), nullable=True)
    narrative = Column(Text, nullable=False)  # The story/reframing
    social_proof = Column(Text, nullable=True)  # Evidence
    authority_claim = Column(String(200), nullable=True)  # Expert backing

    # Psychological leverage
    cognitive_bias_leveraged = Column(String(100), nullable=True)  # anchoring, availability, etc
    emotional_trigger = Column(String(100), nullable=True)  # fear, desire, belonging, etc
    call_to_action = Column(String(200), nullable=False)

    # Targeting
    target_audience_segment = Column(String(100), nullable=True)
    personalization_angle = Column(String(200), nullable=True)

    # Performance
    impression_count = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    perception_shift_measured = Column(Float, default=0)  # Actual movement
    conversion_lift = Column(Float, default=0)  # % sales increase
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class ValuePerceptionOptimizer(Base):
    __tablename__ = "value_perception_optimizers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Current state
    base_price = Column(Float, nullable=False)
    perceived_value = Column(Float, nullable=False)  # What customers think it's worth
    value_gap = Column(Float)  # price vs perceived (if negative, seen as overpriced)

    # Optimization tactics
    anchoring_high_price = Column(Float, nullable=True)  # "Compare to $500 alternative"
    bundled_value_add = Column(Text, nullable=True)  # Free things adding to perceived value
    comparison_competitors = Column(JSONB, default=list)  # [{"competitor": "X", "price": 1000}]

    # Reframing options
    reframe_as_investment = Column(Text, nullable=True)  # Not cost, but investment
    reframe_as_time_saved = Column(Text, nullable=True)  # Value in hours saved
    reframe_as_risk_reduction = Column(Text, nullable=True)  # Safety/insurance value

    # Results
    optimized_perception = Column(Float)  # Predicted new perceived value
    recommended_price = Column(Float)  # Price that matches perception
    expected_conversion_increase = Column(Float)  # % increase if repositioned

    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PerceptionNarrative(Base):
    __tablename__ = "perception_narratives"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Narrative elements
    hero = Column(String(200))  # Who is the hero? (product or customer)
    villain = Column(String(200))  # What problem/competitor?
    transformation = Column(Text)  # Before/after customer story
    proof_points = Column(JSONB, default=list)  # Evidence: [testimonials, metrics, awards]
    emotional_appeal = Column(String(100))  # Pride, belonging, fear, joy, etc
    call_to_identity = Column(String(200))  # "Be someone who..." (identity-based)

    # Variant narratives
    narrative_variants = Column(JSONB, default=list)  # [{"segment": "luxury", "narrative": "..."}]
    primary_narrative = Column(Text)
    backup_narrative = Column(Text, nullable=True)

    # Engagement metrics
    share_count = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0)  # -1 to 1 (negative to positive)
    persuasion_score = Column(Float, default=0)  # 0-1 how persuasive

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
