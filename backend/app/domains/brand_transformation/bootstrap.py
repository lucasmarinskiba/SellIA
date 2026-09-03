"""Create the brand_transformation tables at startup.

Migrations are disabled in this deployment (see backend/entrypoint.sh) and the
CoreBase-wide create_all is intentionally skipped. These models have a tiny,
self-contained FK graph (only -> businesses), so we create just those tables
here, each in its own transaction so one failure never poisons the rest.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)

# Additive columns introduced after the tables' first ship. `t.create(checkfirst=True)`
# only CREATEs missing tables — it never ALTERs an existing one — so on a DB that
# already has the v1 tables these must be added explicitly. Postgres
# `ADD COLUMN IF NOT EXISTS` is idempotent and safe to run every startup.
_COLUMN_PATCHES: list[str] = [
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS compared_to_diagnosis_id UUID",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS score_delta INTEGER",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS confidence INTEGER DEFAULT 0",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS frameworks_applied JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS generated_by VARCHAR(12) DEFAULT 'unknown'",
    # Etapa 0 deepening — DiagnosisAgent v2
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS evidence_snapshot JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS commoditization_analysis JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS referent_gap JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS closest_precedent JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS moat_assessment JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS quick_wins JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS structural_moves JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS kill_criteria JSONB",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS second_order_risk TEXT",
    "ALTER TABLE bt_diagnoses ADD COLUMN IF NOT EXISTS evidence_quality VARCHAR(20)",
    # Etapa 1 deepening — PositioningAgent v2
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS elevator_pitch TEXT",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS alternatives_matrix JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS attribute_value_proof JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS enemy_analysis JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS pov_validation JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS category_decision JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS reframe JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS messaging_pillars JSONB",
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS migration_risks JSONB",
    # Etapa 2 deepening — BrandIdentityAgent v2
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS archetype_analysis JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS verbal_identity JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS naming JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS story_spine JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS taglines_alt JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS identity_consistency_rules JSONB",
    # Etapa 3 deepening — BusinessModelAgent v2
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS model_diagnosis JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS pattern_evaluation JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS canvas_changes JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS value_equation JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS unit_economics_targets JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS pricing_migration JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS rollout JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS risks JSONB",
    "ALTER TABLE bt_business_model_redesigns ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    # Etapa 4 deepening — FOMOEngineAgent v2
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS lever_selection JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS ethics_review JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS activation_sequence JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS content_hooks JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS measurement JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS integration_notes JSONB",
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS risk_matrix JSONB",
    # Etapa 5 deepening — GoToMarketAgent v2
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS loop_evaluation JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS channel_plan JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS content_engine JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS week_1_actions JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS budget_shape JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS anti_goals JSONB",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS north_star_metric VARCHAR(255)",
    "ALTER TABLE bt_gtm_plans ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    # Etapa 6 deepening — RestructuringAgent v2
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS capability_gaps JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS decision_rights JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS operating_rhythm JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS unit_economics_gate JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS operating_plan_90d JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS transition_risks JSONB",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS the_one_hire TEXT",
    "ALTER TABLE bt_restructuring_plans ADD COLUMN IF NOT EXISTS alternative_angles JSONB",
    # Etapa 7 deepening — roadmap synthesis v2
    "ALTER TABLE bt_transformation_programs ADD COLUMN IF NOT EXISTS execution_plan JSONB",
    "ALTER TABLE bt_transformation_programs ADD COLUMN IF NOT EXISTS coherence_audit JSONB",
    # FOMO bridge — deployed campaign links
    "ALTER TABLE bt_fomo_playbooks ADD COLUMN IF NOT EXISTS deployed_campaigns JSONB",
    # Automations v2 — history + alerting
    "ALTER TABLE bt_automations ADD COLUMN IF NOT EXISTS run_history JSONB",
    "ALTER TABLE bt_automations ADD COLUMN IF NOT EXISTS last_severity VARCHAR(12)",
    "ALTER TABLE bt_automations ADD COLUMN IF NOT EXISTS last_alert BOOLEAN DEFAULT FALSE",
    # Bridges — positioning -> competitive, brand identity -> content/assets
    "ALTER TABLE bt_positioning_statements ADD COLUMN IF NOT EXISTS deployed_competitive JSONB",
    "ALTER TABLE bt_brand_identities ADD COLUMN IF NOT EXISTS deployed_assets JSONB",
]


async def ensure_brand_transformation_tables() -> None:
    from app.core.database import engine  # noqa: WPS433 (late import)
    from app.domains.brand_transformation.models import BRAND_TRANSFORMATION_TABLES

    created = 0
    for table in BRAND_TRANSFORMATION_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "brand_transformation bootstrap: table %s skipped: %s",
                table.name, str(e)[:160],
            )

    patched = 0
    for stmt in _COLUMN_PATCHES:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            patched += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("brand_transformation bootstrap: column patch skipped (%s): %s", stmt[:60], str(e)[:120])

    logger.info(
        "✅ brand_transformation tables ensured (%s/%s, %s/%s column patches)",
        created, len(BRAND_TRANSFORMATION_TABLES), patched, len(_COLUMN_PATCHES),
    )
