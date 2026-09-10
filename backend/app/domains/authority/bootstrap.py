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
