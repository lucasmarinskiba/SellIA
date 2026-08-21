"""Phase X8: Auto-Marketing & Growth Agent - SellIA Self-Promotion System."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Enum
from app.db.models import Base
import enum


class MarketingChannel(str, enum.Enum):
    INSTAGRAM = "instagram"  # @sell_.ia
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    EMAIL = "email"
    YOUTUBE = "youtube"
    BLOG = "blog"
    PODCAST = "podcast"
    PARTNERSHIPS = "partnerships"


class ContentType(str, enum.Enum):
    CAROUSEL = "carousel"  # Multi-slide posts
    REEL = "reel"  # Video content (Instagram/TikTok)
    STORY = "story"  # Ephemeral content
    POST = "post"  # Standard post
    ARTICLE = "article"  # Long-form content
    CASE_STUDY = "case_study"  # Customer success story
    TESTIMONIAL = "testimonial"  # Customer testimonial video
    BEHIND_THE_SCENES = "behind_the_scenes"  # Company culture
    EDUCATIONAL = "educational"  # How-to, tips
    FUNNY = "funny"  # Meme/relatable humor


class ContentPillar(str, enum.Enum):
    RESULTS = "results"  # "X% increase in sales"
    TRANSFORMATION = "transformation"  # Before/after stories
    EDUCATION = "education"  # Teaching value
    SOCIAL_PROOF = "social_proof"  # Customer testimonials
    PRODUCT_FEATURES = "product_features"  # Feature highlights
    CULTURE = "culture"  # Team, mission, values
    PROBLEM_SOLVING = "problem_solving"  # Pain point solutions
    URGENCY = "urgency"  # Limited time offers
    HUMOR = "humor"  # Relatable/funny content


class AutoMarketingContent(Base):
    __tablename__ = "auto_marketing_content"
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # Content basics
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)  # Full content
    content_type = Column(Enum(ContentType), nullable=False)
    pillar = Column(Enum(ContentPillar), nullable=False)

    # Channel targeting
    primary_channel = Column(Enum(MarketingChannel), nullable=False)
    secondary_channels = Column(JSON, default=list)  # [linkedin, email, blog]

    # Messaging
    hook = Column(String(300), nullable=False)  # Opening line to grab attention
    cta = Column(String(200), nullable=False)  # Call-to-action
    hashtags = Column(JSON, default=list)  # [#SellIA, #Sales, #AI]
    emoji_strategy = Column(String(100))  # Which emojis for engagement

    # Psychology
    emotion_triggered = Column(String(50))  # aspiration, urgency, belonging, etc
    cognitive_bias = Column(String(50))  # What bias does this trigger?

    # Performance
    status = Column(String(20), default="draft")  # draft, scheduled, published
    publish_datetime = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)

    # Metrics
    impressions = Column(Integer, default=0)
    engagements = Column(Integer, default=0)  # Likes + comments + shares
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)  # Signups from this post
    engagement_rate = Column(Float, default=0)  # engagement / impressions
    conversion_rate = Column(Float, default=0)  # conversions / clicks

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class CustomerSuccessStory(Base):
    __tablename__ = "customer_success_stories"
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # Customer info (anonymized or with permission)
    customer_name = Column(String(200))
    company_name = Column(String(200))
    industry = Column(String(100))
    customer_type = Column(String(50))  # startup, scaleup, enterprise

    # Results (before/after)
    problem_statement = Column(Text)  # What problem did they have?
    solution_applied = Column(Text)  # How SellIA helped
    result_metrics = Column(JSON)  # {sales_increase: "150%", time_saved: "20 hours/week"}
    result_summary = Column(String(300))  # Punchy summary

    # Content variants
    short_story = Column(Text)  # Instagram/TikTok version (280 chars)
    medium_story = Column(Text)  # LinkedIn version (500 chars)
    long_story = Column(Text)  # Blog/case study version
    video_script = Column(Text)  # Testimonial video script

    # Performance
    usage_count = Column(Integer, default=0)  # How many times featured
    total_impressions = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class GrowthHackingExperiment(Base):
    __tablename__ = "growth_hacking_experiments"
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # Experiment definition
    hypothesis = Column(Text)  # "If we post testimonials, engagement will increase 40%"
    tactic = Column(String(100))  # "customer_testimonials", "short_form_video", "influencer_collab"
    channel = Column(Enum(MarketingChannel))
    variant_a = Column(Text)  # Control version
    variant_b = Column(Text)  # Test version

    # Results
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20))  # running, completed, paused

    # Metrics
    variant_a_impressions = Column(Integer, default=0)
    variant_a_conversions = Column(Integer, default=0)
    variant_b_impressions = Column(Integer, default=0)
    variant_b_conversions = Column(Integer, default=0)

    # Analysis
    winner = Column(String(20))  # "variant_a", "variant_b", "tie"
    conversion_lift = Column(Float)  # % improvement
    statistical_significance = Column(Float)  # Confidence level

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class InfluencerCollaboration(Base):
    __tablename__ = "influencer_collaborations"
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # Influencer info
    influencer_name = Column(String(200))
    platform = Column(Enum(MarketingChannel))
    handle = Column(String(100))  # @username
    follower_count = Column(Integer)
    engagement_rate = Column(Float)
    niche = Column(String(100))  # "SaaS", "Marketing", "Entrepreneurship"

    # Collaboration details
    content_type = Column(Enum(ContentType))
    key_message = Column(Text)
    deliverables = Column(JSON)  # [post, story, reel, etc]
    compensation = Column(String(100))  # "Free plan", "$1000", "Revenue share"

    # Performance
    status = Column(String(20))  # proposed, confirmed, live, completed
    impressions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    roi = Column(Float, default=0)  # Revenue / investment

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class GrowthMetrics(Base):
    __tablename__ = "growth_metrics"
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # Channel performance
    channel = Column(Enum(MarketingChannel))
    date = Column(DateTime(timezone=True))

    # Daily metrics
    posts_published = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    follower_growth = Column(Integer, default=0)

    # Calculated rates
    engagement_rate = Column(Float, default=0)
    click_through_rate = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    cost_per_acquisition = Column(Float, default=0)  # If paid

    # Trend
    trend_vs_yesterday = Column(Float)  # % change
    trend_vs_week_ago = Column(Float)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
