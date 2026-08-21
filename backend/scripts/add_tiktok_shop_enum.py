"""One-off: add TIKTOK_SHOP to the Postgres channelplatform enum.

Por qué existe este script en vez de una migración de Alembic normal: la
cadena de migraciones de este repo ya está rota antes de este cambio
(`alembic heads` falla con KeyError sobre un down_revision que no matchea
ningún archivo existente) — no es algo que este cambio haya introducido.
Corregir esa cadena es un trabajo aparte; mientras tanto, este script hace
exactamente el ALTER TYPE necesario, de forma segura e idempotente.

ALTER TYPE ... ADD VALUE es aditivo y no bloqueante en Postgres (no reescribe
filas existentes, no requiere downtime). Safe de correr en producción.

Uso (desde el shell de Render, Dashboard -> srv-d9p6tlt3erlc73bvfdbg -> Shell):
    python scripts/add_tiktok_shop_enum.py
"""
import asyncio
import os
import sys

import asyncpg


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está seteada en este entorno.", file=sys.stderr)
        sys.exit(1)

    # asyncpg no entiende el prefijo postgres+asyncpg:// que usa SQLAlchemy
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")

    conn = await asyncpg.connect(dsn)
    try:
        existing = await conn.fetch(
            "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'channelplatform'::regtype ORDER BY enumsortorder;"
        )
        labels = [r["enumlabel"] for r in existing]
        print(f"Valores actuales del enum channelplatform ({len(labels)}): {labels}")

        if "TIKTOK_SHOP" in labels:
            print("TIKTOK_SHOP ya existe en el enum. Nada que hacer.")
            return

        await conn.execute("ALTER TYPE channelplatform ADD VALUE 'TIKTOK_SHOP';")
        print("✅ TIKTOK_SHOP agregado al enum channelplatform.")

        confirm = await conn.fetch(
            "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'channelplatform'::regtype ORDER BY enumsortorder;"
        )
        print(f"Valores finales ({len(confirm)}): {[r['enumlabel'] for r in confirm]}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
