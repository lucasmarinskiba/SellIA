"""Orchestrator types — multi-domain decision models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    """Decision priority hierarchy."""
    PRESERVE_CASH = "preserve_cash"  # runway < 30 days
    STABILIZE = "stabilize"  # runway 30–60 days
    BALANCED = "balanced"  # runway 60–90 days
    GROWTH = "growth"  # runway > 90 days


class Action(str, Enum):
    """Executable actions."""
    REALLOCATE_AD_BUDGET = "reallocate_ad_budget"  # shift across channels
    REDUCE_AD_SPEND = "reduce_ad_spend"  # lower daily budget %
    CUT_OPEX = "cut_opex"  # reduce operating expense
    DELAY_PAYMENT = "delay_payment"  # negotiate payment terms
    ACCELERATE_COLLECTION = "accelerate_collection"  # push customer payments


@dataclass
class BusinessMetrics:
    """Real-time snapshot of business state."""
    cash_balance: Decimal
    runway_days: Optional[int]
    forecast_revenue_30d: Decimal
    forecast_confidence: Decimal  # 0–1 (q90-q10) / q50
    current_monthly_opex: Decimal
    current_gross_margin: Decimal
    highest_roas_channel: str
    lowest_roas_channel: str
    ad_spend_daily: Decimal
    priority: Priority


@dataclass
class Recommendation:
    """Single action recommendation."""
    action: Action
    rationale: str
    target_value: Optional[Decimal] = None  # e.g., new budget % or OpEx reduction %
    confidence: Decimal = Decimal("0.5")  # 0–1
    impact_cash_30d: Optional[Decimal] = None  # estimated impact
    impact_revenue_30d: Optional[Decimal] = None


@dataclass
class OrchestratorPlan:
    """Complete decision plan."""
    business_id: str
    metrics: BusinessMetrics
    priority: Priority
    recommendations: list[Recommendation] = field(default_factory=list)
    scenario_name: str = "current_state"
    approved_actions: list[Action] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reasoning: str = ""


@dataclass
class Scenario:
    """What-if scenario for planning."""
    name: str  # e.g., "ad_spend_+25%", "opex_-15%"
    description: str
    changes: dict  # {"ad_spend_daily": 0.25, "opex_pct": -0.15}
    projected_cash_30d: Decimal
    projected_revenue_30d: Decimal
    projected_runway_days: Optional[int]
    feasibility: str  # "easy" | "moderate" | "hard"
    risks: list[str] = field(default_factory=list)
