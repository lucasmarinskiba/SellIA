"""Create the authority tables at startup (migrations are disabled here)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_authority_tables() -> None:
    from app.core.database import engine
    from app.domains.authority.models import AUTHORITY_TABLES

    tables = list(AUTHORITY_TABLES)

    # The E-E-A-T tables (platform_reviews, testimonials, awards, …) were never
    # created by anything: every call to GET /authority/trust-score has been
    # 500ing with "relation does not exist" since it was written, silently,
    # because the page that calls it catches the error and shows "todavía no
    # hay reseñas". They are the source of the prueba_social pillar, so they
    # get created here.
    try:
        from app.models.authority_building import (
            Award, Review, SellerBio, Testimonial, TrustScore,
        )
        tables += [
            Testimonial.__table__, Award.__table__, Review.__table__,
            TrustScore.__table__, SellerBio.__table__,
        ]
    except Exception as e:  # noqa: BLE001
        logger.warning("authority bootstrap: E-E-A-T models unavailable: %s", str(e)[:160])

    for table in tables:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("authority bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ authority tables ensured (%s)", len(tables))
    await _migrate_impact_score()


async def _migrate_impact_score() -> None:
    """impact_points (int) -> impact_score (float).

    The column used to hold a hand-written constant, so an integer was enough.
    It now holds a projection replayed from the pillar's own formula, which
    lands on 4.7 as often as on 5 -- an integer column would silently truncate
    every one of those to a rounder, wronger number. create(checkfirst=True)
    never alters an existing table, so the change is applied explicitly here.
    """
    from sqlalchemy import text

    from app.core.database import engine

    statements = [
        # Rename only if the old column is the one that exists.
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'authority_actions' AND column_name = 'impact_points')
               AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'authority_actions' AND column_name = 'impact_score')
            THEN
                ALTER TABLE authority_actions RENAME COLUMN impact_points TO impact_score;
            END IF;
        END $$;
        """,
        """
        ALTER TABLE authority_actions
        ALTER COLUMN impact_score TYPE double precision
        USING impact_score::double precision;
        """,
    ]
    for statement in statements:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(statement))
        except Exception as e:  # noqa: BLE001
            logger.warning("authority bootstrap: impact_score migration: %s", str(e)[:160])
