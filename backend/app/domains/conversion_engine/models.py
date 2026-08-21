"""Phase X12: Conversion & Attraction Agent - Multi-Touch Closing Sequences."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from app.db.models import Base


class ConversionSequence(Base):
    __tablename__ = "conversion_sequences"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    # Prospect status
    deal_stage = Column(String(50), nullable=False)  # aware, considering, demoing, negotiating, closed
    estimated_deal_value = Column(Float, default=0)
    probability_to_close = Column(Float, default=0)  # 0-1.0
    days_in_cycle = Column(Integer, default=0)

    # Multi-touch sequence
    touch_1_type = Column(String(50))  # email, demo_invite, content
    touch_1_sent = Column(DateTime(timezone.utc), nullable=True)
    touch_1_opened = Column(Boolean, default=False)

    touch_2_type = Column(String(50))
    touch_2_sent = Column(DateTime(timezone.utc), nullable=True)
    touch_2_result = Column(String(50))  # opened, clicked, demo_scheduled

    touch_3_type = Column(String(50))
    touch_3_sent = Column(DateTime(timezone.utc), nullable=True)

    touch_4_type = Column(String(50))
    touch_4_sent = Column(DateTime(timezone.utc), nullable=True)

    # Closing tactics
    last_closing_angle = Column(String(255))  # ROI-focused, risk-reduction, competitive-advantage
    objection_handling = Column(JSON, default=list)  # ["price", "implementation_time"]
    competitor_positioning = Column(Text, nullable=True)  # How we position vs. competitor

    # Results
    demo_scheduled = Column(Boolean, default=False)
    demo_date = Column(DateTime(timezone.utc), nullable=True)
    contract_sent = Column(Boolean, default=False)
    contract_signed = Column(Boolean, default=False)
    closed_value = Column(Float, default=0)

    # Attribution
    which_touch_converted = Column(Integer, default=0)  # 1, 2, 3, 4
    conversion_attributed_to_tactic = Column(String(100))  # "urgency", "ROI", "social_proof"

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone.utc), nullable=True)


class AttractionMagnet(Base):
    __tablename__ = "attraction_magnets"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    # Lead magnet / gated content
    magnet_type = Column(String(50), nullable=False)  # ebook, calculator, template, webinar, audit
    magnet_title = Column(String(255), nullable=False)
    magnet_promise = Column(String(255))  # "Get 40% more sales in 90 days"

    # Targeting
    ideal_customer_profile = Column(String(100))  # "SaaS founders", "Sales VPs", "B2B marketers"
    industries_targeted = Column(JSON, default=list)
    company_size_range = Column(String(100))  # "10-100", "100-1000"

    # Conversion optimization
    cta_copy = Column(String(200))  # "Get my free audit"
    form_fields = Column(JSON, default=list)  # ["email", "company", "role"]
    estimated_conversion_rate = Column(Float, default=0.15)  # 15%

    # Performance
    downloads_total = Column(Integer, default=0)
    emails_captured = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0)  # Leads who watched video / opened PDF
    demo_requests_from_magnet = Column(Integer, default=0)

    # Follow-up sequence
    follow_up_email_1_delay_hours = Column(Integer, default=1)
    follow_up_email_1_subject = Column(String(200))
    followup_email_2_delay_hours = Column(Integer, default=24)
    followup_email_3_delay_hours = Column(Integer, default=72)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
