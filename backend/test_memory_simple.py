#!/usr/bin/env python
"""
Simplified test: MultiUser Memory Isolation (no ORM dependencies)

Uses raw SQL to create test users + memory.

Usage:
  python test_memory_simple.py
"""

import os
import sys
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.domains.user_memory.models import UserMemory, UserMemoryEvent
from app.domains.user_memory.service import UserMemoryService
from app.domains.user_memory.schemas import UserMemoryUpdate, UserMemoryEventCreate
from app.core.security import get_password_hash


async def test_memory_isolation():
    """Test multi-user memory isolation"""
    logger.info("═" * 60)
    logger.info("Multi-User Memory Isolation Test (Simplified)")
    logger.info("═" * 60)

    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as db:
        try:
            # Test 1: DB Connection
            logger.info("\n[Test 1/5] Database Connection")
            result = await db.execute(text("SELECT 1"))
            assert result.scalar() == 1
            logger.info("✓ Database OK")

            # Test 2: Create users via raw SQL (bypass ORM)
            logger.info("\n[Test 2/5] Create Test Users (Raw SQL)")

            user_a_id = str(uuid.uuid4())
            user_b_id = str(uuid.uuid4())

            hashed_pass = get_password_hash("test123")

            # Insert users directly into DB
            await db.execute(text("""
                INSERT INTO users (id, email, full_name, hashed_password, is_active, email_verified, created_at, updated_at)
                VALUES
                  (:id_a, :email_a, 'User A', :pass, true, true, now(), now()),
                  (:id_b, :email_b, 'User B', :pass, true, true, now(), now())
            """), {
                "id_a": user_a_id,
                "email_a": f"test-a-{uuid.uuid4().hex[:8]}@test.local",
                "id_b": user_b_id,
                "email_b": f"test-b-{uuid.uuid4().hex[:8]}@test.local",
                "pass": hashed_pass,
            })
            await db.commit()
            logger.info(f"✓ User A: {user_a_id}")
            logger.info(f"✓ User B: {user_b_id}")

            # Test 3: Create memories
            logger.info("\n[Test 3/5] Create User Memories")

            service_a = UserMemoryService(db)
            service_b = UserMemoryService(db)

            memory_a = await service_a.get_or_create(uuid.UUID(user_a_id))
            memory_b = await service_b.get_or_create(uuid.UUID(user_b_id))

            logger.info(f"✓ Memory A: {memory_a.id}")
            logger.info(f"✓ Memory B: {memory_b.id}")

            # Test 4: Update with different data
            logger.info("\n[Test 4/5] Update Memories with Different Data")

            # User A: ecommerce, growth
            update_a = UserMemoryUpdate(
                industry_focus="ecommerce",
                business_stage="growth",
                preferred_tone="aggressive",
                preferred_language="es",
            )
            memory_a = await service_a.update_memory(uuid.UUID(user_a_id), update_a)
            await service_a.add_interest(uuid.UUID(user_a_id), "conversion")
            await service_a.add_interest(uuid.UUID(user_a_id), "facebook_ads")
            await service_a.add_challenge(uuid.UUID(user_a_id), "cart_abandonment")
            logger.info("✓ User A: ecommerce, growth, interests=[conversion, ads]")

            # User B: services, mature
            update_b = UserMemoryUpdate(
                industry_focus="professional_services",
                business_stage="mature",
                preferred_tone="professional",
                preferred_language="pt",
            )
            memory_b = await service_b.update_memory(uuid.UUID(user_b_id), update_b)
            await service_b.add_interest(uuid.UUID(user_b_id), "retention")
            await service_b.add_interest(uuid.UUID(user_b_id), "email_marketing")
            await service_b.add_challenge(uuid.UUID(user_b_id), "employee_scaling")
            logger.info("✓ User B: services, mature, interests=[retention, email]")

            # Test 5: Log events
            logger.info("\n[Test 5/5] Log Events & Verify Isolation")

            for i in range(3):
                event = UserMemoryEventCreate(
                    event_type="message_sent",
                    event_data={"topic": "conversion"},
                )
                await service_a.log_event(uuid.UUID(user_a_id), event)
            logger.info("✓ User A: 3 events logged")

            for i in range(2):
                event = UserMemoryEventCreate(
                    event_type="message_sent",
                    event_data={"topic": "retention"},
                )
                await service_b.log_event(uuid.UUID(user_b_id), event)
            logger.info("✓ User B: 2 events logged")

            # Verify isolation
            logger.info("\n[Isolation Verification]")

            result_a = await db.execute(select(UserMemory).where(UserMemory.user_id == uuid.UUID(user_a_id)))
            memory_a = result_a.scalar_one()
            result_b = await db.execute(select(UserMemory).where(UserMemory.user_id == uuid.UUID(user_b_id)))
            memory_b = result_b.scalar_one()

            # User A checks
            assert memory_a.industry_focus == "ecommerce"
            assert memory_a.business_stage == "growth"
            assert "conversion" in memory_a.key_interests
            assert "facebook_ads" in memory_a.key_interests
            assert "cart_abandonment" in memory_a.key_challenges
            assert memory_a.total_messages == 3
            assert memory_a.preferred_language == "es"
            logger.info("✓ User A data verified")

            # User B checks
            assert memory_b.industry_focus == "professional_services"
            assert memory_b.business_stage == "mature"
            assert "retention" in memory_b.key_interests
            assert "email_marketing" in memory_b.key_interests
            assert "employee_scaling" in memory_b.key_challenges
            assert memory_b.total_messages == 2
            assert memory_b.preferred_language == "pt"
            logger.info("✓ User B data verified")

            # Cross-check: isolation
            assert "conversion" not in memory_b.key_interests
            assert "cart_abandonment" not in memory_b.key_challenges
            assert "retention" not in memory_a.key_interests
            assert "employee_scaling" not in memory_a.key_challenges
            logger.info("✓ Isolation verified (no cross-contamination)")

            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("✅ ALL TESTS PASSED")
            logger.info("=" * 60)
            logger.info(f"\nUser A ({user_a_id}):")
            logger.info(f"  Industry: {memory_a.industry_focus}")
            logger.info(f"  Stage: {memory_a.business_stage}")
            logger.info(f"  Interests: {', '.join(memory_a.key_interests)}")
            logger.info(f"  Challenges: {', '.join(memory_a.key_challenges)}")
            logger.info(f"  Messages: {memory_a.total_messages}")
            logger.info(f"\nUser B ({user_b_id}):")
            logger.info(f"  Industry: {memory_b.industry_focus}")
            logger.info(f"  Stage: {memory_b.business_stage}")
            logger.info(f"  Interests: {', '.join(memory_b.key_interests)}")
            logger.info(f"  Challenges: {', '.join(memory_b.key_challenges)}")
            logger.info(f"  Messages: {memory_b.total_messages}")

            return True

        except AssertionError as e:
            logger.error(f"✗ Assertion failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def main():
    success = await test_memory_isolation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
