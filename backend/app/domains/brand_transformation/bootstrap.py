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
