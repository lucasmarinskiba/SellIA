"""One-off: add the publish-tracking columns to the live instagram_posts table.

instagram_posts was first created on production before the "real posting"
feature (graph_publisher.py + FOMO Intelligence wiring) added 5 new columns
to the model: publish_status, fomo_application_id, ig_media_id,
ig_permalink, publish_error. create_all()'s IF NOT EXISTS never ALTERs an
already-existing table, so the live table never got them - confirmed via a
real 500 on production: asyncpg.exceptions.UndefinedColumnError, column
"publish_status" of relation "instagram_posts" does not exist.

All 5 are nullable/defaulted, so this is a safe additive ALTER TABLE -
no data loss, no lock beyond the brief DDL operation.

Uso: python scripts/add_instagram_posts_columns.py
"""
import asyncio
import os

import asyncpg

COLUMNS_TO_ADD = [
    ("publish_status", "VARCHAR(30) DEFAULT 'draft'"),
    ("fomo_application_id", "VARCHAR(36)"),
    ("ig_media_id", "VARCHAR(100)"),
    ("ig_permalink", "VARCHAR(500)"),
    ("publish_error", "TEXT"),
]


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está seteada.")
        return

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    try:
        for column, coltype in COLUMNS_TO_ADD:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.columns "
                "WHERE table_name = 'instagram_posts' AND column_name = $1)",
                column,
            )
            if exists:
                print(f"OK   instagram_posts.{column}: ya existe")
                continue

            # column/coltype come from the hardcoded COLUMNS_TO_ADD list
            # above, not from any external/runtime input — no user-supplied
            # value ever reaches this f-string. One-off admin script, run
            # manually, not wired to any endpoint.
            await conn.execute(f"ALTER TABLE instagram_posts ADD COLUMN {column} {coltype}")
            print(f"ADDED instagram_posts.{column} {coltype}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
