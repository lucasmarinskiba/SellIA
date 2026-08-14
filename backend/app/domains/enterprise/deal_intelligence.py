"""Phase 26c: Deal Intelligence - Scoring, Forecasting, Risk Analysis."""

from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from datetime import datetime, timedelta
import uuid

from app.database import Base


class DealScore(Base):
    """Win probability per deal (ML-powered scoring)."""
    __tablename__ = "deal_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = Column(String(255), nullable=False, unique=True)
    seller_id = Column(String(255), nullable=False)

    # Core signals
    win_probability = Column(Float, default=0.5)  # 0-1
    confidence_level = Column(Float, default=0.0)  # 0-1 model confidence

    # Scoring components
    stage_score = Column(Float, default=0)  # Days in stage
    engagement_score = Column(Float, default=0)  # Interaction velocity
    proposal_score = Column(Float, default=0)  # Proposal sent/responded
    competition_score = Column(Float, default=0)  # Competitor threat level
    timing_score = Column(Float, default=0)  # Buying cycle alignment

    # Risk indicators
    is_at_risk = Column(Boolean, default=False)
    risk_reason = Column(Text, nullable=True)  # "No response in 7d", "Competitor signal", etc
    days_since_last_contact = Column(Float, nullable=True)

    # Trend
    score_trend = Column(String(20), default="stable")  # up, down, stable

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_deal_score', 'seller_id', 'win_probability'),
        Index('idx_at_risk', 'seller_id', 'is_at_risk'),
    )


class ForecastSnapshot(Base):
    """Daily revenue forecast snapshot."""
    __tablename__ = "forecast_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(255), nullable=False)
    forecast_date = Column(DateTime, default=datetime.utcnow)

    # Aggregates
    total_pipeline_value = Column(Float, default=0)
    weighted_pipeline = Column(Float, default=0)  # pipeline * win_probability

    # Forecast (next 30, 60, 90 days)
    projected_revenue_30d = Column(Float, default=0)
    projected_revenue_60d = Column(Float, default=0)
    projected_revenue_90d = Column(Float, default=0)

    # Confidence
    confidence_level = Column(Float, default=0)
    accuracy_vs_actual = Column(Float, nullable=True)  # For backtesting

    # Deal breakdown
    deal_breakdown = Column(JSON, nullable=True)  # {prob_bucket: count, ...}

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_forecast_seller', 'seller_id', 'forecast_date'),
    )


class WinLossAnalysis(Base):
    """Post-close analysis: why deals won or lost."""
    __tablename__ = "win_loss_analysis"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id = Column(String(255), nullable=False)
    seller_id = Column(String(255), nullable=False)

    # Outcome
    outcome = Column(String(20), nullable=False)  # won, lost, stalled
    final_value = Column(Float, nullable=True)

    # Contributing factors
    primary_reason = Column(String(255), nullable=False)
    secondary_reasons = Column(Text, nullable=True)  # CSV list

    # Seller actions that helped/hurt
    actions_taken = Column(Text, nullable=True)  # List of key actions
    days_to_close = Column(Float, nullable=True)

    # Learnings for future deals
    teachable_moments = Column(Text, nullable=True)  # Tactical + strategic

    competitor_mentioned = Column(String(255), nullable=True)
    price_was_factor = Column(Boolean, default=False)
    timing_was_factor = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_win_loss', 'seller_id', 'outcome'),
    )


class DealIntelligenceManager:
    """Business logic for deal scoring & forecasting."""

    @staticmethod
    def calculate_deal_score(
        days_in_stage: float,
        engagement_velocity: float,  # touches per day
        proposal_status: str,  # none, sent, responding, negotiating
        competitor_signals: int,  # count of competitor mentions
        buyer_authority: float,  # 0-1
    ) -> float:
        """Calculate win probability (0-1) for deal."""
        score = 0.5  # base

        # Stage: more days = higher risk
        if days_in_stage < 7:
            score += 0.1
        elif days_in_stage > 30:
            score -= 0.2

        # Engagement: velocity matters
        if engagement_velocity > 2.0:  # 2+ touches/day
            score += 0.15
        elif engagement_velocity < 0.2:  # <0.2 touches/day
            score -= 0.15

        # Proposal: sent/responding wins
        if proposal_status == "negotiating":
            score += 0.20
        elif proposal_status == "responding":
            score += 0.10
        elif proposal_status == "sent":
            score += 0.05

        # Competition: threats reduce score
        if competitor_signals > 2:
            score -= min(0.25, competitor_signals * 0.05)

        # Authority: decision maker present
        score += buyer_authority * 0.15

        return max(0.0, min(1.0, score))

    @staticmethod
    def forecast_revenue(deals: list[dict]) -> dict:
        """Forecast 30/60/90 day revenue from deal list."""
        total_pipeline = sum(d.get("value", 0) for d in deals)
        weighted_pipeline = sum(d.get("value", 0) * d.get("win_prob", 0.5) for d in deals)

        # Simple forecast: weighted * close probability over time
        close_velocity = 0.3  # 30% of deals close in 30d (tunable)

        return {
            "total_pipeline": total_pipeline,
            "weighted_pipeline": weighted_pipeline,
            "projected_revenue_30d": weighted_pipeline * close_velocity,
            "projected_revenue_60d": weighted_pipeline * (close_velocity * 1.5),
            "projected_revenue_90d": weighted_pipeline * (close_velocity * 2.0),
        }
