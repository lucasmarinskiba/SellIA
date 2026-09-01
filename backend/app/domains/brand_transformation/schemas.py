"""Brand Transformation schemas — request / response models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ----------------------------- requests -----------------------------

class BusinessProfileIn(BaseModel):
    """Shared context payload most agents accept."""

    industry: str
    what_they_sell: str
    current_positioning: str | None = None
    known_competitors: list[str] = []
    revenue_model: str | None = None
    target_customer: str | None = None
    price_point: str | None = None
    notes: str | None = None


class DiagnosisIn(BusinessProfileIn):
    """Etapa 0 input. Every extra field is optional but each one raises the
    diagnosis from 'thin' toward 'solid' evidence quality."""

    time_in_market: str | None = None            # e.g. "3 years"
    monthly_revenue: str | None = None           # free-form, e.g. "~$40k"
    gross_margin_pct: float | None = None
    repeat_purchase_rate: str | None = None      # e.g. "18%"
    pricing: list[str] = []                      # ["Bag 250g $12", "Wholesale $9/kg"]
    channels: list[str] = []                     # ["own store", "Instagram", "2 wholesale accounts"]
    differentiation_claims: list[str] = []       # what they currently tell customers
    customer_quotes: list[str] = []              # verbatim review / feedback snippets
    recent_marketing: list[str] = []             # what they've tried lately


class StageRunIn(BaseModel):
    """Advance / run a single stage inside a program."""

    profile: BusinessProfileIn | None = None
    extra_instructions: str | None = None


class ProgramCreateIn(BaseModel):
    name: str = "Brand Transformation"
    profile: BusinessProfileIn


class AutomationIn(BaseModel):
    automation_type: str
    schedule: str = "monthly"
    config: dict | None = None


# ----------------------------- responses -----------------------------

class DiagnosisOut(_ORM):
    id: UUID
    industry: str
    referent_potential_score: int
    commoditization_level: str
    symptoms: list | None
    root_causes: list | None
    highest_leverage_moves: list | None
    scorecard: dict | None
    summary: str | None
    commoditization_analysis: dict | None
    referent_gap: dict | None
    closest_precedent: dict | None
    moat_assessment: dict | None
    quick_wins: list | None
    structural_moves: list | None
    kill_criteria: list | None
    second_order_risk: str | None
    evidence_quality: str | None
    evidence_snapshot: dict | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    compared_to_diagnosis_id: UUID | None
    score_delta: int | None
    created_at: datetime


class PositioningOut(_ORM):
    id: UUID
    competitive_alternatives: list | None
    unique_attributes: list | None
    value_themes: list | None
    best_fit_customers: list | None
    market_category: str | None
    new_category_name: str | None
    point_of_view: str | None
    the_enemy: str | None
    positioning_statement: str | None
    one_liner: str | None
    elevator_pitch: str | None
    alternative_angles: list | None
    alternatives_matrix: list | None
    attribute_value_proof: list | None
    enemy_analysis: dict | None
    pov_validation: dict | None
    category_decision: dict | None
    reframe: dict | None
    messaging_pillars: list | None
    migration_risks: dict | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class BrandIdentityOut(_ORM):
    id: UUID
    primary_archetype: str | None
    secondary_archetype: str | None
    rename_recommended: bool
    name_candidates: list | None
    tagline: str | None
    manifesto: str | None
    voice_attributes: list | None
    voice_do: list | None
    voice_dont: list | None
    sample_rewrites: list | None
    visual_brief: dict | None
    brand_architecture: str | None
    alternative_angles: list | None
    archetype_analysis: dict | None
    verbal_identity: dict | None
    naming: dict | None
    story_spine: dict | None
    taglines_alt: list | None
    identity_consistency_rules: list | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class BusinessModelOut(_ORM):
    id: UUID
    canvas: dict | None
    applied_patterns: list | None
    new_revenue_streams: list | None
    grand_slam_offer: dict | None
    pricing_architecture: dict | None
    errc_grid: dict | None
    rationale: str | None
    model_diagnosis: dict | None
    pattern_evaluation: list | None
    canvas_changes: list | None
    value_equation: dict | None
    unit_economics_targets: dict | None
    pricing_migration: dict | None
    rollout: dict | None
    risks: list | None
    alternative_angles: list | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class FOMOPlaybookOut(_ORM):
    id: UUID
    mechanisms: list | None
    launch_ritual: dict | None
    cadence: str | None
    risk_notes: str | None
    alternative_angles: list | None
    lever_selection: list | None
    ethics_review: dict | None
    activation_sequence: dict | None
    content_hooks: list | None
    measurement: dict | None
    integration_notes: list | None
    risk_matrix: list | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class GTMPlanOut(_ORM):
    id: UUID
    primary_growth_loop: dict | None
    channels: list | None
    lightning_strike: dict | None
    funnel: dict | None
    content_pillars: list | None
    plan_90_days: list | None
    loop_evaluation: list | None
    channel_plan: list | None
    content_engine: dict | None
    week_1_actions: list | None
    budget_shape: dict | None
    anti_goals: list | None
    north_star_metric: str | None
    alternative_angles: list | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class RestructuringOut(_ORM):
    id: UUID
    kill: list | None
    keep: list | None
    scale: list | None
    org_redesign: str | None
    core_processes: list | None
    promise_kpis: list | None
    unit_economics_notes: str | None
    confidence: int
    frameworks_applied: list | None
    generated_by: str
    created_at: datetime


class ProgramOut(_ORM):
    id: UUID
    name: str
    status: str
    current_stage: str
    completed_stages: list | None
    stage_artifacts: dict | None
    roadmap: dict | None
    metrics_board: dict | None
    created_at: datetime
    updated_at: datetime


class AutomationOut(_ORM):
    id: UUID
    automation_type: str
    schedule: str
    config: dict | None
    is_active: bool
    last_run_at: datetime | None
    last_result: dict | None
    runs_count: int
    created_at: datetime


class StageResultOut(BaseModel):
    """Returned by the orchestrator after running one stage."""

    program_id: UUID
    stage_key: str
    stage_name: str
    artifact_id: UUID | None
    artifact: dict
    next_stage: str | None
    completed_stages: list[str]


class StageInfoOut(BaseModel):
    key: str
    order: int
    name: str
    goal: str
    agent: str
    deliverable: str
