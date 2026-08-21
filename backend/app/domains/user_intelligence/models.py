"""Phase X9: AI User Intelligence Agent - Deep User Profiling."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from app.db.models import Base
import enum


class UserPersonalityType(str, enum.Enum):
    EARLY_ADOPTER = "early_adopter"  # Tech-savvy, innovation-focused
    PRAGMATIST = "pragmatist"  # ROI-focused, practical
    SKEPTIC = "skeptic"  # Needs proof, data-driven
    IMPULSE_BUYER = "impulse_buyer"  # Fast decision-maker, FOMO-responsive
    ANALYST = "analyst"  # Research-heavy, comparison-focused
    SOCIAL_PROOF_SEEKER = "social_proof_seeker"  # Influenced by others
    STATUS_CONSCIOUS = "status_conscious"  # Premium/exclusivity-focused
    VALUE_MAXIMIZER = "value_maximizer"  # Price/benefit conscious


class UserMotivationType(str, enum.Enum):
    REVENUE_GROWTH = "revenue_growth"
    TIME_SAVING = "time_saving"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"
    COST_REDUCTION = "cost_reduction"
    TEAM_PRODUCTIVITY = "team_productivity"
    RISK_MITIGATION = "risk_mitigation"
    BRAND_BUILDING = "brand_building"
    CUSTOMER_SATISFACTION = "customer_satisfaction"


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    # User identification
    user_id = Column(String(36), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    company_name = Column(String(255))

    # Personality & behavior
    personality_type = Column(String(50), nullable=False)  # early_adopter, pragmatist, etc
    risk_aversion_score = Column(Float, default=5.0)  # 1-10, higher = more risk-averse
    decision_velocity = Column(Float, default=5.0)  # 1-10, faster = more impulse
    social_proof_sensitivity = Column(Float, default=5.0)  # 1-10, higher = responds to social

    # Motivation & pain points
    primary_motivation = Column(String(50))
    secondary_motivations = Column(JSON, default=list)  # [revenue_growth, time_saving]
    stated_pain_points = Column(JSON, default=list)  # ["sales cycles too long", "low conversion"]
    inferred_pain_points = Column(JSON, default=list)  # AI-inferred from behavior

    # Purchase behavior
    average_deal_size = Column(Float, nullable=True)
    purchase_frequency = Column(String(50))  # one-time, quarterly, recurring
    is_budget_approved = Column(Boolean, default=False)
    buying_committee_size = Column(Integer, default=1)

    # Engagement signals
    content_consumption_pattern = Column(String(50))  # video, case_study, webinar, etc
    email_open_rate = Column(Float, default=0)
    click_through_rate = Column(Float, default=0)
    demo_interest_level = Column(Float, default=0)  # 0-1.0

    # FOMO & urgency sensitivity
    scarcity_responsiveness = Column(Float, default=5.0)  # 1-10
    deadline_sensitivity = Column(Float, default=5.0)  # 1-10
    social_proof_impact = Column(Float, default=5.0)  # 1-10
    exclusivity_appeal = Column(Float, default=5.0)  # 1-10

    # AI-generated insights
    next_best_action = Column(String(255))  # "send case study", "invite to webinar"
    estimated_conversion_probability = Column(Float, default=0)  # 0-1.0
    recommended_messaging = Column(String(255))  # ROI-focused, risk-reduction, social proof
    churn_risk_score = Column(Float, default=0)  # 0-1.0, for existing customers

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UserJourneyStage(Base):
    __tablename__ = "user_journey_stages"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    stage = Column(String(50), nullable=False)  # awareness, consideration, decision, onboarding, retention
    entry_date = Column(DateTime(timezone.utc), nullable=False)
    exit_date = Column(DateTime(timezone.utc), nullable=True)

    # Stage-specific metrics
    stage_duration_days = Column(Integer, default=0)
    engagement_score = Column(Float, default=0)  # 0-1.0
    momentum = Column(String(50))  # accelerating, steady, stalling, churning

    # Triggers & events
    last_touchpoint = Column(String(255))
    touchpoint_count_this_stage = Column(Integer, default=0)
    next_recommended_touchpoint = Column(String(255))

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
