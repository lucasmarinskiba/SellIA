"""Brand Transformation models — diagnosis, positioning, brand identity,
business model, FOMO playbook, GTM plan, restructuring plan, staged program,
and automations.

CoreBase domain (app.core.database.Base). Small FK graph: everything points
only at businesses.id. Provisioned at startup via bootstrap.ensure_brand_transformation_tables
(migrations are disabled in this deployment — see backend/entrypoint.sh).
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, ForeignKey, func, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BrandDiagnosis(Base):
    """Etapa 0 output — why the business is mediocre + Referent Potential Score."""

    __tablename__ = "bt_diagnoses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    # Input snapshot
    industry: Mapped[str] = mapped_column(String(120))
    current_positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_competitors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    revenue_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Input — structured evidence the caller supplied (drives confidence)
    evidence_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Output — headline
    referent_potential_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    commoditization_level: Mapped[str] = mapped_column(String(20), default="unknown")  # low/medium/high/severe
    symptoms: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["undifferentiated pricing", ...]
    root_causes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    highest_leverage_moves: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # top 3
    scorecard: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {positioning: 2, brand: 1, ...}
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Output — deep lenses
    commoditization_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # per dimension: price/product/distribution/brand
    referent_gap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # per axis: current / referent looks like / the gap
    closest_precedent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {brand, why, what_to_copy, what_not_to_copy}
    moat_assessment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {has_moat, buildable_moat_type, how}
    quick_wins: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # <=30-day moves
    structural_moves: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 6-12 month moves
    kill_criteria: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # signals => don't chase referent status, pivot
    second_order_risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_quality: Mapped[str | None] = mapped_column(String(20), nullable=True)  # thin/partial/solid — how grounded the call is

    # Quality/provenance (draft->critique->refine pass — see service._draft_then_refine)
    confidence: Mapped[int] = mapped_column(Integer, default=0)  # 0-100, self-assessed rigor
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    # Trend tracking (populated by the rediagnosis automation)
    compared_to_diagnosis_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("bt_diagnoses.id", ondelete="SET NULL"), nullable=True
    )
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PositioningStatement(Base):
    """Etapa 1 output — Dunford positioning + category design."""

    __tablename__ = "bt_positioning_statements"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    competitive_alternatives: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    unique_attributes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    value_themes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    best_fit_customers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    market_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_category_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    point_of_view: Mapped[str | None] = mapped_column(Text, nullable=True)
    the_enemy: Mapped[str | None] = mapped_column(Text, nullable=True)
    positioning_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    one_liner: Mapped[str | None] = mapped_column(String(400), nullable=True)
    elevator_pitch: Mapped[str | None] = mapped_column(Text, nullable=True)  # ~30s spoken version
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2-3 genuinely different bets

    # v2 deep lenses
    alternatives_matrix: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{alternative, why_tolerated, what_customer_keeps, what_they_lose}]
    attribute_value_proof: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{attribute, value, proof_point}]
    enemy_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {enemy, test_results[], passes}
    pov_validation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {who_nods, who_bristles, cost_to_hold, evidence, scores}
    category_decision: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {recommendation: play|design, rationale, king_test, name_candidates[]}
    reframe: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {from, to}
    messaging_pillars: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{pillar, proof}]
    migration_risks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {who_we_lose, acceptable, mitigation}

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BrandIdentity(Base):
    """Etapa 2 output — archetype, name, voice, visual brief."""

    __tablename__ = "bt_brand_identities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    primary_archetype: Mapped[str | None] = mapped_column(String(60), nullable=True)
    secondary_archetype: Mapped[str | None] = mapped_column(String(60), nullable=True)
    rename_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    name_candidates: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manifesto: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_attributes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    voice_do: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    voice_dont: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sample_rewrites: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    visual_brief: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {mood, palette_direction, typography, imagery}
    brand_architecture: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2-3 alternate archetype/voice bets

    # v2 deep lenses
    archetype_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {shortlist:[{archetype,fit,differentiation,authenticity}], primary, secondary, blend}
    verbal_identity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {attributes:[{adj,sounds_like,not}], lexicon:{use,ban}, rhythm, humor, rules}
    naming: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {decision, rationale, candidates:[{name,idea,scores}], name_test}
    story_spine: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {world, problem, insight, mission}
    taglines_alt: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 3 alternate taglines
    identity_consistency_rules: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 5 non-negotiables (feeds brand_consistency_monitor)

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BusinessModelRedesign(Base):
    """Etapa 3 output — new canvas + patterns + grand-slam offer + pricing."""

    __tablename__ = "bt_business_model_redesigns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    canvas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # 9 blocks
    applied_patterns: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["subscription", "razor_and_blade"]
    new_revenue_streams: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    grand_slam_offer: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {dream_outcome, bonuses, guarantee, ...}
    pricing_architecture: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # tiers, anchors, psych tactics
    errc_grid: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # eliminate/reduce/raise/create
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # v2 deep lenses
    model_diagnosis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {how_it_earns_now, margin_leaks, starts_from_zero, fragility}
    pattern_evaluation: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # scored shortlist of candidate patterns
    canvas_changes: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{block, from, to, why, forces_change_in}]
    value_equation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # quantified Hormozi
    unit_economics_targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {gross_margin, cac_ceiling, payback_months, ltv_cac, contribution_margin} each w/ assumption
    pricing_migration: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # how to move from current pricing without revolt
    rollout: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {change_first, validate_before, sequence}
    risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # cannibalization / ops load / churn-if-wrong
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2 different model bets

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FOMOPlaybook(Base):
    """Etapa 4 output — desire/scarcity engine tuned to this business."""

    __tablename__ = "bt_fomo_playbooks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    mechanisms: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # [{lever, why_it_fits, implementation, trigger, kpi, measurement, anti_fake_guardrail, honest_alternative}]
    launch_ritual: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cadence: Mapped[str | None] = mapped_column(String(120), nullable=True)  # e.g. "weekly drop, Thursday 11:00"
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2-3 alternate lever combos

    # v2 deep lenses
    lever_selection: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # all 7 levers scored on FOMO_LEVER_AXES + chosen bool
    ethics_review: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {the_line_for_this_brand, never_do[], shown_from_inside_test}
    activation_sequence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {first, gating_conditions, ramp_90d}
    content_hooks: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{mechanism, copy_angle}] — reusable by GTM/copy
    measurement: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {leading[], lagging[]}
    integration_notes: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{mechanism, sellia_domain_action}] via FOMO_DOMAIN_MAP
    risk_matrix: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{mechanism, backfire_mode, early_warning, kill_switch}]
    deployed_campaigns: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{mechanism, lever, campaign_id, campaign_type, status}] — set by fomo_bridge

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GTMPlan(Base):
    """Etapa 5 output — go-to-market + growth loop + launch script."""

    __tablename__ = "bt_gtm_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    primary_growth_loop: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {type, steps, reinvestment, turning_metric, cycle_time}
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{channel, role, first_action}] (kept for back-compat)
    lightning_strike: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # launch sequence
    funnel: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_pillars: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    plan_90_days: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # milestones w/ owner + metric + depends_on

    # v2 deep lenses
    loop_evaluation: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # loop types scored on GROWTH_LOOP_AXES
    channel_plan: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{channel, role, hypothesis, first_action, effort, leading_signal, kill_signal}]
    content_engine: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {pillars, formats, cadence, repurposing_chain, owner}
    week_1_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 3 concrete
    budget_shape: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {allocation, constraint}
    anti_goals: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # what NOT to do in 90 days
    north_star_metric: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2 different GTM bets

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RestructuringPlan(Base):
    """Etapa 6 output — kill/keep/scale + org + core processes + KPIs."""

    __tablename__ = "bt_restructuring_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    kill: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{what, why, sunk_cost_rebuttal, frees, who_pushes_back}]
    keep: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{what, why, risk_if_dropped}]
    scale: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{what, why, first_constraint, prereq}]
    org_redesign: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_processes: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{name, owner, trigger, steps, sla, promise_protected, failure_mode}]
    promise_kpis: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # metrics that prove the brand promise
    unit_economics_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # v2 deep lenses
    capability_gaps: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{gap, build_buy_borrow, reason}]
    decision_rights: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{decision, owner, consulted, informed}]
    operating_rhythm: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {daily, weekly, monthly, quarterly} each {purpose, attendees, output}
    unit_economics_gate: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {must_hold[], pause_growth_trigger}
    operating_plan_90d: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{change, owner, done_looks_like, depends_on}]
    transition_risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{risk, mitigation}]
    the_one_hire: Mapped[str | None] = mapped_column(Text, nullable=True)  # the single role that unblocks the most
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2 org bets (lean vs hire-ahead)

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(12), default="unknown")  # llm | fallback | unknown

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransformationProgram(Base):
    """The staged program that ties all etapas together for a business."""

    __tablename__ = "bt_transformation_programs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(200), default="Brand Transformation")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/paused/completed
    current_stage: Mapped[str] = mapped_column(String(40), default="diagnosis")
    completed_stages: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["diagnosis", ...]
    stage_artifacts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {stage_key: artifact_id}
    roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {north_star, horizons{90,180,365}, workstreams, sequencing_logic}
    execution_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {dependency_graph, critical_path, decision_gates, kill_switches, resourcing, leading_indicators, first_2_weeks}
    coherence_audit: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {score, checks:[{check, verdict, contradiction, fix}], must_fix_before_launch[]}
    metrics_board: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BrandAutomation(Base):
    """Standing automations for brand/marketing upkeep."""

    __tablename__ = "bt_automations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    automation_type: Mapped[str] = mapped_column(String(50))
    # rediagnosis | brand_consistency_monitor | fomo_cadence | positioning_drift_watch | competitor_narrative_watch
    schedule: Mapped[str] = mapped_column(String(40), default="monthly")  # weekly/monthly/quarterly
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    runs_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


BRAND_TRANSFORMATION_TABLES = [
    BrandDiagnosis.__table__,
    PositioningStatement.__table__,
    BrandIdentity.__table__,
    BusinessModelRedesign.__table__,
    FOMOPlaybook.__table__,
    GTMPlan.__table__,
    RestructuringPlan.__table__,
    TransformationProgram.__table__,
    BrandAutomation.__table__,
]
