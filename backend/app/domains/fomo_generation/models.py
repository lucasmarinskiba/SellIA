"""Phase X10: FOMO Generation Agent - Personalized Scarcity & Urgency."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from app.db.models import Base


class FOMOCampaign(Base):
    __tablename__ = "fomo_campaigns"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    # Campaign type
    fomo_type = Column(String(50), nullable=False)  # scarcity, urgency, social_proof, exclusivity, loss_aversion
    fomo_strategy = Column(String(255))  # "only_3_seats_left", "deadline_friday", "150_companies_using"

    # Messaging
    subject_line = Column(String(200), nullable=False)
    body_message = Column(Text, nullable=False)
    cta_text = Column(String(100), nullable=False)
    urgency_level = Column(Integer, default=1)  # 1-10, higher = more aggressive

    # Timing
    triggered_at = Column(DateTime(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone.utc), nullable=True)
    time_until_deadline_hours = Column(Integer, default=24)

    # Personalization
    personality_type = Column(String(50))  # Which type of user this targets
    motivation_type = Column(String(50))  # ROI, speed, exclusivity
    scarcity_metric = Column(String(100))  # "3 seats", "$500 discount", "24 hours"
    social_proof_stat = Column(String(100))  # "150 companies", "Rated #1", "4.9/5"

    # Performance
    sent_at = Column(DateTime(timezone.utc), nullable=True)
    opened_at = Column(DateTime(timezone.utc), nullable=True)
    clicked_at = Column(DateTime(timezone.utc), nullable=True)
    converted = Column(Boolean, default=False)

    # Attribution
    revenue_attributed = Column(Float, default=0)
    fomo_contribution_score = Column(Float, default=0)  # 0-1.0, how much FOMO drove conversion

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class CountdownTrigger(Base):
    __tablename__ = "countdown_triggers"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    trigger_type = Column(String(50))  # pricing_expires, cohort_closes, limited_offer
    trigger_event = Column(String(255))  # "Founding price: $99/mo → $299/mo in 48 hours"

    countdown_start = Column(DateTime(timezone.utc), nullable=False)
    countdown_end = Column(DateTime(timezone.utc), nullable=False)
    hours_remaining = Column(Integer, nullable=False)

    # Messages sent at milestones
    sent_24h_warning = Column(Boolean, default=False)
    sent_6h_warning = Column(Boolean, default=False)
    sent_1h_final = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
