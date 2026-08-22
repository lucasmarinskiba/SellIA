#!/usr/bin/env python
"""Initialize test database with UserMemory tables"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.core.database import Base


async def init_db():
    """Create all tables"""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Tables created")
    await engine.dispose()


asyncio.run(init_db())
