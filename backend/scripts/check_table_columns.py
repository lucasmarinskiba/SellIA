"""One-off: inspect actual columns of a table on the live Postgres DB.

Diagnostic only — no writes. Uso:
    python scripts/check_table_columns.py <table_name>
"""
import asyncio
import os
import sys

import asyncpg


async def main() -> None:
    if len(sys.argv) < 2:
        print("ERROR: uso: python scripts/check_table_columns.py <table_name>", file=sys.stderr)
        sys.exit(1)

    table_name = sys.argv[1]
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está seteada.", file=sys.stderr)
        sys.exit(1)

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    try:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table_name,
        )
        if not exists:
            print(f"Tabla '{table_name}' NO existe.")
            return

        rows = await conn.fetch(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = $1 ORDER BY ordinal_position",
            table_name,
        )
        print(f"Columnas de '{table_name}' ({len(rows)}):")
        for r in rows:
            print(f"  - {r['column_name']} ({r['data_type']})")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
