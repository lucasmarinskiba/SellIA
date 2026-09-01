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

    # Output
    referent_potential_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    commoditization_level: Mapped[str] = mapped_column(String(20), default="unknown")  # low/medium/high/severe
    symptoms: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["undifferentiated pricing", ...]
    root_causes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    highest_leverage_moves: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # top 3
    scorecard: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {positioning: 2, brand: 1, ...}
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quality/provenance (draft->critique->refine pass — see service._draft_then_refine)
    confidence: Mapped[int] = mapped_column(Integer, default=0)  # 0-100, self-assessed rigor
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

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
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2-3 genuinely different bets

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

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

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

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

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FOMOPlaybook(Base):
    """Etapa 4 output — desire/scarcity engine tuned to this business."""

    __tablename__ = "bt_fomo_playbooks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    mechanisms: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # [{lever, why_it_fits, implementation, kpi, anti_fake_guardrail}]
    launch_ritual: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cadence: Mapped[str | None] = mapped_column(String(120), nullable=True)  # e.g. "weekly drop, Thursday 11:00"
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternative_angles: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # 2-3 alternate lever combos

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GTMPlan(Base):
    """Etapa 5 output — go-to-market + growth loop + launch script."""

    __tablename__ = "bt_gtm_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    primary_growth_loop: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {type, steps, reinvestment}
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{channel, role, first_action}]
    lightning_strike: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # launch sequence
    funnel: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_pillars: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    plan_90_days: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # week-by-week or milestone list

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RestructuringPlan(Base):
    """Etapa 6 output — kill/keep/scale + org + core processes + KPIs."""

    __tablename__ = "bt_restructuring_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)

    kill: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    keep: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    scale: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    org_redesign: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_processes: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{name, owner, sla, why}]
    promise_kpis: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # metrics that prove the brand promise
    unit_economics_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_applied: Mapped[list | None] = mapped_column(JSONB, nullable=True)

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
    roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {"90": [...], "180": [...], "365": [...]}
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
