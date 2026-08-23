#!/usr/bin/env python3
"""
Create all required tables directly (bypass Alembic if needed).
Usage: python create_tables.py
"""
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.database import Base
from app.domains.users.models import User
from app.domains.user_memory.models import UserMemory, UserMemoryEvent, UserPreference

async def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    db_url = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")

    if not db_url:
        print("❌ DATABASE_URL not set")
        return False

    print(f"📡 Connecting to: {db_url[:50]}...")

    try:
        engine = create_async_engine(db_url, echo=False)

        # Create all tables from models
        print("🔨 Creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tables created successfully!")

        # Verify
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

        print(f"\n📊 Tables in database ({len(tables)} total):")
        for table in sorted(tables):
            if table.startswith("user"):
                print(f"   ✓ {table}")

        expected = ["users", "user_memory", "user_memory_events", "user_preferences"]
        for exp in expected:
            if exp in tables:
                print(f"   ✓ {exp} exists")
            else:
                print(f"   ❌ {exp} MISSING")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(create_all_tables())
    exit(0 if result else 1)
