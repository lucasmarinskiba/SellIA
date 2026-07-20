"""Init script para crear tablas extendidas de Computer Use.

Ejecutar: python -m backend.scripts.init_computer_use_extended
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, Base

# Import all base models so SQLAlchemy knows about referenced tables
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.computer_use.models import ComputerUseSession
from app.domains.computer_use.models_extended import (
    ComputerUseTemplate,
    ComputerUseScheduledTask,
    ComputerUseAnnotation,
    ComputerUseBrowserProfile,
    ComputerUseProxyConfig,
    ComputerUseSessionShare,
    ComputerUseBatchJob,
    ComputerUseSessionTag,
    ComputerUseSessionBookmark,
    ComputerUseSessionNote,
    ComputerUseWebhook,
)


async def init_tables():
    async with engine.begin() as conn:
        # SQLAlchemy's create_all resolves dependencies and creates in correct order
        await conn.run_sync(Base.metadata.create_all)
        print("OK: All tables created (or already exist)")

    # Verify which extended tables exist
    from sqlalchemy import inspect
    def get_tables(sync_conn):
        inspector = inspect(sync_conn)
        return inspector.get_table_names()

    async with engine.connect() as conn:
        tables = await conn.run_sync(get_tables)

    extended_tables = [
        "computer_use_templates",
        "computer_use_scheduled_tasks",
        "computer_use_annotations",
        "computer_use_browser_profiles",
        "computer_use_proxy_configs",
        "computer_use_session_shares",
        "computer_use_batch_jobs",
        "computer_use_session_tags",
        "computer_use_session_bookmarks",
        "computer_use_session_notes",
        "computer_use_webhooks",
    ]

    created = [t for t in extended_tables if t in tables]
    print(f"Extended tables ready: {created}")
    print(f"Total tables in DB: {len(tables)}")


if __name__ == "__main__":
    asyncio.run(init_tables())
