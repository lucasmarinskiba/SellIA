"""Social Seller models — vendedores virtuales por plataforma."""
import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, JSON, Text, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SocialSeller(Base):
    __tablename__ = "social_sellers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # instagram, tiktok, facebook, whatsapp, twitter, threads, linkedin, etc.
    name = Column(String(100), nullable=False)  # e.g. "Zoe", "TikTok Tom"
    avatar_url = Column(Text, nullable=True)
    personality_slug = Column(String(100), nullable=True)  # references AgentPersonality
    voice_config = Column(JSONB, default=dict, nullable=False)  # tone, emojis, catch_phrases, response_speed
    stats = Column(JSONB, default=dict, nullable=False)  # total_sales, revenue, conversion_rate, loyal_customers
    status = Column(String(20), default="active", nullable=False)  # active, paused, training
    ai_auto_reply = Column(Boolean, default=True, nullable=False)
    greeting_message = Column(Text, nullable=True)
    closing_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SellerCustomerRelationship(Base):
    __tablename__ = "seller_customer_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("social_sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    # Note: using conversation_id as customer proxy for now. In future will link to unified_customers
    first_contact_at = Column(DateTime(timezone=True), nullable=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    total_interactions = Column(Integer, default=0, nullable=False)
    deals_closed = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Numeric(14, 2), default=0, nullable=False)
    relationship_stage = Column(String(30), default="first_contact", nullable=False)  # first_contact, nurturing, proposal, closed, loyal, advocate
    loyalty_score = Column(Integer, default=0, nullable=False)  # 0-100
    next_best_action = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UnifiedCustomer(Base):
    __tablename__ = "unified_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(200), nullable=True)
    master_email = Column(String(255), nullable=True, index=True)
    master_phone = Column(String(50), nullable=True, index=True)
    identity_map = Column(JSONB, default=dict, nullable=False)  # {"instagram": "ig_id", "whatsapp": "phone", "tiktok": "tt_id"}
    first_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    total_lifetime_value = Column(Numeric(14, 2), default=0, nullable=False)
    buying_frequency_days = Column(Integer, nullable=True)  # avg days between purchases
    preferred_platforms = Column(JSONB, default=list, nullable=False)  # ordered by engagement
    rfm_segment = Column(String(30), nullable=True)  # Champion, Loyal, Potential, New, At Risk, Lost
    last_purchase_at = Column(DateTime(timezone=True), nullable=True)
    total_purchases = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SellerPerformance(Base):
    __tablename__ = "seller_performances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("social_sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(20), nullable=False)  # day, week, month
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    leads_acquired = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)
    conversations_active = Column(Integer, default=0, nullable=False)
    deals_won = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(14, 2), default=0, nullable=False)
    conversion_rate = Column(Numeric(5, 2), default=0, nullable=False)
    best_performing_hour = Column(Integer, nullable=True)  # 0-23
    best_performing_content_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CustomerLoyaltyBadge(Base):
    __tablename__ = "customer_loyalty_badges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_type = Column(String(50), nullable=False)  # champion, ambassador, fan_1, comeback_kid, early_bird, big_spender, regular
    name = Column(String(100), nullable=False)  # "Campeón", "Embajador", "Fan #1"
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    criteria = Column(JSONB, default=dict, nullable=False)  # { "min_purchases": 5, "min_ltv": 1000 }
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CustomerBadgeAssignment(Base):
    __tablename__ = "customer_badge_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("customer_loyalty_badges.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    awarded_by_seller_id = Column(UUID(as_uuid=True), ForeignKey("social_sellers.id", ondelete="SET NULL"), nullable=True)
