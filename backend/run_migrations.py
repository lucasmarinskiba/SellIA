#!/usr/bin/env python
"""
Run Alembic migrations on Railway deployment.

Usage:
  python run_migrations.py

This script checks the current DB schema and applies any pending migrations.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.database import engine, Base
from sqlalchemy import text


async def check_db_connection():
    """Verify database connection is working"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


async def create_alembic_version_table():
    """Ensure alembic_version table exists"""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    PRIMARY KEY (version_num)
                )
            """))
            await conn.commit()
            logger.info("✓ alembic_version table ready")
        except Exception as e:
            logger.warning(f"alembic_version table check: {e}")


def run_migrations():
    """Run Alembic migrations using synchronous interface"""
    settings = get_settings()

    # Convert async URL to sync for Alembic
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Setup Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    try:
        logger.info("Running Alembic migrations...")
        command.upgrade(alembic_cfg, "heads")
        logger.info("✓ Migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main migration runner"""
    logger.info("Starting migration process...")

    # Check DB connection
    if not await check_db_connection():
        logger.error("Cannot connect to database. Exiting.")
        sys.exit(1)

    # Ensure alembic table exists
    await create_alembic_version_table()

    # Run migrations
    success = run_migrations()

    if success:
        logger.info("✓ All done! SellIA backend is ready.")
        sys.exit(0)
    else:
        logger.error("✗ Migration failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
