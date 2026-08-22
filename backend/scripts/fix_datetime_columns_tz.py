"""One-off: convert naive TIMESTAMP columns to TIMESTAMP WITH TIME ZONE.

Why this exists: fomo_intelligence and instagram_automation models declared
several datetime columns as bare Column(DateTime, ...) while every Python
default passed a timezone-aware value (datetime.now(timezone.utc)). SQLite
(used for all local testing this session) silently tolerated the mismatch;
Postgres correctly rejects it - asyncpg.exceptions.DataError, "can't
subtract offset-naive and offset-aware datetimes" - confirmed live via a
real 500 on POST /api/v1/instagram-automation/create-feedia-post.

The Python model is already fixed to Column(DateTime(timezone=True), ...),
but that only affects future CREATE TABLE calls - it does not retroactively
ALTER an already-existing table, same class of gap as the earlier TikTok
Shop enum fix.

ALTER COLUMN ... TYPE ... USING col AT TIME ZONE 'UTC' is safe here because
every row so far was written by this same buggy code path, which always
computed UTC values before the tz-naive column silently dropped the
offset - reattaching 'UTC' is the correct, lossless conversion, not a
guess.

Uso: python scripts/fix_datetime_columns_tz.py
"""
import asyncio
import os

import asyncpg

# (table, column) pairs that need TIMESTAMP WITHOUT TIME ZONE -> WITH TIME ZONE
COLUMNS_TO_FIX = [
    ("fomo_strategy_applications", "applied_at"),
    ("fomo_strategy_outcomes", "measured_at"),
    ("fomo_strategy_intelligence", "last_updated"),
    ("instagram_posts", "posted_at"),
    ("instagram_posts", "scheduled_for"),
    ("instagram_posts", "created_at"),
    ("instagram_campaigns", "created_at"),
    ("instagram_campaigns", "launched_at"),
    ("instagram_campaigns", "ended_at"),
    ("instagram_audiences", "first_interaction_at"),
    ("instagram_audiences", "last_interaction_at"),
    ("instagram_audiences", "created_at"),
    ("instagram_conversion_paths", "instagram_interaction_at"),
    ("instagram_conversion_paths", "landing_page_visit_at"),
    ("instagram_conversion_paths", "lead_created_at"),
    ("instagram_conversion_paths", "trial_started_at"),
    ("instagram_conversion_paths", "demo_scheduled_at"),
    ("instagram_conversion_paths", "deal_closed_at"),
    ("instagram_conversion_paths", "created_at"),
]


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está seteada.")
        return

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    try:
        for table, column in COLUMNS_TO_FIX:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.columns "
                "WHERE table_name = $1 AND column_name = $2)",
                table, column,
            )
            if not exists:
                print(f"SKIP {table}.{column}: no existe (tabla no creada todavía, no hay nada que migrar)")
                continue

            current_type = await conn.fetchval(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = $1 AND column_name = $2",
                table, column,
            )
            if current_type == "timestamp with time zone":
                print(f"OK   {table}.{column}: ya es timestamptz")
                continue

            await conn.execute(
                f'ALTER TABLE {table} ALTER COLUMN {column} '
                f"TYPE TIMESTAMP WITH TIME ZONE USING {column} AT TIME ZONE 'UTC'"
            )
            print(f"FIXED {table}.{column}: {current_type} -> timestamp with time zone")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
