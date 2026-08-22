"""Phase X11: Loyalty & Retention Agent - Personalized Retention Sequences."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from app.db.models import Base


class LoyaltyProgram(Base):
    # x11_loyalty_status, no "loyalty_programs": ese nombre ya lo usan dos
    # modelos preexistentes (app.domains.loyalty.loyalty_models y
    # app.domains.retention.models), ambos modelando la CONFIGURACIÓN de un
    # programa de loyalty por negocio (points_per_dollar, thresholds) - algo
    # completamente distinto al estado de loyalty POR USUARIO que trackea
    # esta clase. Confirmado en producción: la tabla real "loyalty_programs"
    # ya existía con esa otra columna (business_id, points_per_dollar, etc),
    # sin "user_id" - toda query de este modelo fallaba con
    # UndefinedColumnError contra el schema equivocado.
    __tablename__ = "x11_loyalty_status"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    # Loyalty tier
    tier = Column(String(50), default="bronze")  # bronze, silver, gold, platinum
    points_balance = Column(Float, default=0)
    referral_bonus_available = Column(Boolean, default=True)

    # Engagement metrics
    total_usage_hours = Column(Float, default=0)
    feature_adoption_score = Column(Float, default=0)  # 0-1.0
    support_tickets_resolved = Column(Integer, default=0)
    nps_score = Column(Integer, default=0)

    # Retention signals
    login_streak_days = Column(Integer, default=0)
    days_since_last_login = Column(Integer, default=999)
    engagement_trend = Column(String(50))  # increasing, stable, declining
    churn_risk_score = Column(Float, default=0)  # 0-1.0

    # Rewards & incentives
    next_reward_milestone = Column(String(255))  # "Unlock Gold: 5 more team members"
    reward_unlock_progress = Column(Float, default=0)  # 0-1.0
    exclusive_perks = Column(JSON, default=list)  # ["priority_support", "custom_training"]

    # VIP treatment
    dedicated_account_manager = Column(String(255), nullable=True)
    vip_access_features = Column(JSON, default=list)
    personal_success_plan = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RetentionSequence(Base):
    __tablename__ = "retention_sequences"
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    user_id = Column(String(36), nullable=False, index=True)
    sequence_type = Column(String(50), nullable=False)  # win_back, expansion, vip_nurture, churn_prevention
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=5)

    # Sequence messaging
    step_1_message = Column(Text)  # Day 0
    step_2_message = Column(Text)  # Day 3
    step_3_message = Column(Text)  # Day 7
    step_4_message = Column(Text)  # Day 14
    step_5_message = Column(Text)  # Day 30

    # Engagement
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    conversions = Column(Integer, default=0)

    # Status
    started_at = Column(DateTime(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone.utc), nullable=True)
    outcome = Column(String(50))  # success, paused, churned

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
