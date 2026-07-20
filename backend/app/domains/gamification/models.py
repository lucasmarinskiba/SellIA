"""Gamification & Experience Models

Makes the user feel the excitement of a new car, new house, new phone —
the system becomes their HOME. Points, achievements, streaks, levels,
visual business growth, celebrations, and personalized companion.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AchievementCategory(str, enum.Enum):
    SALES = "sales"              # Cerraste tu primera venta, 10 ventas, etc.
    GROWTH = "growth"            # Llegaste a 100 leads, 1000 visitas, etc.
    CONSISTENCY = "consistency"  # Streaks: 7 días seguidos activo
    MASTERY = "mastery"          # Usaste una feature avanzada
    SOCIAL = "social"            # Conseguiste referidos, reviews
    ZEN = "zen"                  # Dejaste que el sistema trabaje por vos
    MILESTONE = "milestone"      # 1 mes, 6 meses, 1 año usando SellIA
    MISSIONS = "missions"        # Completaste misiones, aprobaste estrategias IA


class AchievementTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class UserGamificationProfile(Base):
    """User's gamification profile — levels, points, streaks, overall progress."""
    __tablename__ = "user_gamification_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Level system
    level = Column(Integer, default=1, nullable=False)
    level_title = Column(String(100), default="Emprendedor Novato", nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    xp_to_next_level = Column(Integer, default=100, nullable=False)
    progress_pct = Column(Numeric(5, 2), default=0, nullable=False)  # 0-100

    # Streaks
    current_login_streak = Column(Integer, default=0, nullable=False)
    max_login_streak = Column(Integer, default=0, nullable=False)
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    autopilot_trust_streak = Column(Integer, default=0, nullable=False)  # Días seguidos dejando el piloto automático

    # Stats
    total_achievements = Column(Integer, default=0, nullable=False)
    total_sales_closed = Column(Integer, default=0, nullable=False)
    total_revenue_generated = Column(Numeric(14, 2), default=0, nullable=False)
    total_leads_acquired = Column(Integer, default=0, nullable=False)
    total_content_published = Column(Integer, default=0, nullable=False)
    total_reviews_collected = Column(Integer, default=0, nullable=False)
    total_referrals_generated = Column(Integer, default=0, nullable=False)

    # Mission stats
    total_missions_created = Column(Integer, default=0, nullable=False)
    total_missions_completed = Column(Integer, default=0, nullable=False)
    total_missions_started = Column(Integer, default=0, nullable=False)
    total_computer_use_sessions = Column(Integer, default=0, nullable=False)
    total_platforms_automated = Column(Integer, default=0, nullable=False)

    # Visual "Business Garden" state
    garden_state = Column(JSONB, default=dict, nullable=False)
    # {"trees": 3, "flowers": 12, "buildings": 1, "lights_on": True, "season": "spring"}

    # Companion AI state
    companion_name = Column(String(50), default="Selia", nullable=False)
    companion_mood = Column(String(20), default="happy", nullable=False)  # happy, excited, proud, calm, concerned
    companion_last_message = Column(Text, nullable=True)

    # Mood tracking
    user_mood_today = Column(String(20), nullable=True)  # excited, stressed, calm, tired, motivated
    mood_history = Column(JSONB, default=list, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Achievement(Base):
    """A predefined achievement that users can unlock."""
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(AchievementCategory), nullable=False)
    tier = Column(Enum(AchievementTier), nullable=False, default=AchievementTier.BRONZE)

    # Requirements
    requirement_type = Column(String(50), nullable=False)  # count, streak, threshold, event
    requirement_value = Column(Integer, default=1, nullable=False)
    requirement_context = Column(JSONB, default=dict, nullable=False)

    # Rewards
    xp_reward = Column(Integer, default=10, nullable=False)
    garden_reward = Column(JSONB, default=dict, nullable=False)  # {"tree": 1, "flower": 5}

    # Visual
    icon = Column(String(100), default="trophy", nullable=False)
    color = Column(String(20), default="#FFD700", nullable=False)
    animation = Column(String(50), default="bounce", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)


class UserAchievement(Base):
    """Tracks which achievements a user has unlocked and when."""
    __tablename__ = "user_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)

    unlocked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    was_celebrated = Column(Boolean, default=False, nullable=False)
    shared_to_social = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index('ix_user_achievements_user_achievement', 'user_id', 'achievement_id', unique=True),
    )


class CelebrationEvent(Base):
    """A celebration event — sale, milestone, achievement unlock, etc."""
    __tablename__ = "celebration_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, index=True)  # sale, achievement, milestone, streak, referral, review
    event_title = Column(String(200), nullable=False)
    event_description = Column(Text, nullable=True)
    event_value = Column(Numeric(14, 2), nullable=True)  # Amount sold, etc.
    event_metadata = Column(JSONB, default=dict, nullable=False)

    # Celebration intensity
    intensity = Column(String(20), default="medium", nullable=False)  # small, medium, big, epic
    was_shown = Column(Boolean, default=False, nullable=False)
    shown_at = Column(DateTime(timezone=True), nullable=True)

    # Companion reaction
    companion_message = Column(Text, nullable=True)
    companion_emotion = Column(String(20), default="happy", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_celebration_events_user_unshown', 'user_id', 'was_shown'),
    )


class DailyMoodLog(Base):
    """User's daily mood check-in."""
    __tablename__ = "daily_mood_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    mood = Column(String(20), nullable=False)  # excited, stressed, calm, tired, motivated, grateful
    energy_level = Column(Integer, default=5, nullable=False)  # 1-10
    notes = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)  # Companion's personalized response

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_mood_logs_user_date', 'user_id', 'created_at'),
    )
