#!/usr/bin/env python
"""
Test multi-user memory isolation on Railway.

Runs:
1. Connect to Railway PostgreSQL
2. Create test users
3. Log events to each user's memory
4. Verify isolation (no data bleeding)
5. Check engagement scoring

Usage:
  python test_multi_user_memory.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.domains.users.models import User
from app.domains.user_memory.models import UserMemory, UserMemoryEvent
from app.domains.user_memory.service import UserMemoryService
from app.domains.user_memory.schemas import UserMemoryUpdate, UserMemoryEventCreate
from app.core.security import get_password_hash


async def setup_db():
    """Setup async database connection"""
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
    return engine, async_session


async def test_multi_user_memory():
    """Main test suite"""
    logger.info("═" * 60)
    logger.info("Starting Multi-User Memory Isolation Tests")
    logger.info("═" * 60)

    engine, async_session = await setup_db()

    async with async_session() as db:
        try:
            # Test 1: Database connection
            logger.info("\n[Test 1/5] Database Connection")
            result = await db.execute(text("SELECT 1"))
            assert result.scalar() == 1
            logger.info("✓ Database connection OK")

            # Test 2: Create test users
            logger.info("\n[Test 2/5] Create Test Users")
            user_a = User(
                email=f"test-a-{uuid4().hex[:8]}@sellia.local",
                full_name="Test User A",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
                email_verified=True,
            )
            user_b = User(
                email=f"test-b-{uuid4().hex[:8]}@sellia.local",
                full_name="Test User B",
                hashed_password=get_password_hash("testpass456"),
                is_active=True,
                email_verified=True,
            )
            db.add(user_a)
            db.add(user_b)
            await db.commit()
            await db.refresh(user_a)
            await db.refresh(user_b)
            logger.info(f"✓ User A: {user_a.id}")
            logger.info(f"✓ User B: {user_b.id}")

            # Test 3: Create isolated memories
            logger.info("\n[Test 3/5] Create Isolated User Memories")
            service_a = UserMemoryService(db)
            service_b = UserMemoryService(db)

            memory_a = await service_a.get_or_create(user_a.id)
            memory_b = await service_b.get_or_create(user_b.id)
            logger.info(f"✓ Memory A created: {memory_a.id}")
            logger.info(f"✓ Memory B created: {memory_b.id}")

            # Test 4: Update memories with different data
            logger.info("\n[Test 4/5] Update Memories with Different Data")

            # User A: ecommerce, growth stage
            update_a = UserMemoryUpdate(
                industry_focus="ecommerce",
                business_stage="growth",
                preferred_tone="aggressive",
                preferred_language="es",
            )
            memory_a = await service_a.update_memory(user_a.id, update_a)
            await service_a.add_interest(user_a.id, "conversion_optimization")
            await service_a.add_interest(user_a.id, "facebook_ads")
            await service_a.add_challenge(user_a.id, "cart_abandonment")
            logger.info("✓ User A: ecommerce, growth, interests=[conversion, ads], challenges=[abandonment]")

            # User B: services, mature
            update_b = UserMemoryUpdate(
                industry_focus="professional_services",
                business_stage="mature",
                preferred_tone="professional",
                preferred_language="pt",
            )
            memory_b = await service_b.update_memory(user_b.id, update_b)
            await service_b.add_interest(user_b.id, "client_retention")
            await service_b.add_interest(user_b.id, "email_marketing")
            await service_b.add_challenge(user_b.id, "employee_scaling")
            logger.info("✓ User B: services, mature, interests=[retention, email], challenges=[scaling]")

            # Log events for each user
            logger.info("\n[Test 5/5] Log Events & Verify Isolation")

            # User A events
            for i in range(3):
                event = UserMemoryEventCreate(
                    event_type="message_sent",
                    event_data={"topic": "conversion", "agent": "copywriter"},
                )
                await service_a.log_event(user_a.id, event)
            logger.info("✓ User A: logged 3 messages")

            # User B events
            for i in range(2):
                event = UserMemoryEventCreate(
                    event_type="message_sent",
                    event_data={"topic": "retention", "agent": "strategist"},
                )
                await service_b.log_event(user_b.id, event)
            logger.info("✓ User B: logged 2 messages")

            # Verify isolation
            logger.info("\n[Isolation Verification]")

            # Reload memories
            result_a = await db.execute(select(UserMemory).where(UserMemory.user_id == user_a.id))
            memory_a = result_a.scalar_one()
            result_b = await db.execute(select(UserMemory).where(UserMemory.user_id == user_b.id))
            memory_b = result_b.scalar_one()

            # Check User A data
            assert memory_a.industry_focus == "ecommerce", f"User A industry wrong: {memory_a.industry_focus}"
            assert memory_a.business_stage == "growth", f"User A stage wrong: {memory_a.business_stage}"
            assert "conversion_optimization" in memory_a.key_interests
            assert "facebook_ads" in memory_a.key_interests
            assert "cart_abandonment" in memory_a.key_challenges
            assert memory_a.total_messages == 3, f"User A message count wrong: {memory_a.total_messages}"
            assert memory_a.preferred_language == "es"
            logger.info("✓ User A memory isolated correctly")

            # Check User B data
            assert memory_b.industry_focus == "professional_services", f"User B industry wrong: {memory_b.industry_focus}"
            assert memory_b.business_stage == "mature", f"User B stage wrong: {memory_b.business_stage}"
            assert "client_retention" in memory_b.key_interests
            assert "email_marketing" in memory_b.key_interests
            assert "employee_scaling" in memory_b.key_challenges
            assert memory_b.total_messages == 2, f"User B message count wrong: {memory_b.total_messages}"
            assert memory_b.preferred_language == "pt"
            logger.info("✓ User B memory isolated correctly")

            # Cross-check: User A data NOT in User B
            assert "conversion_optimization" not in memory_b.key_interests
            assert "facebook_ads" not in memory_b.key_interests
            assert "cart_abandonment" not in memory_b.key_challenges
            logger.info("✓ User A data NOT in User B (isolation verified)")

            # Cross-check: User B data NOT in User A
            assert "client_retention" not in memory_a.key_interests
            assert "email_marketing" not in memory_a.key_interests
            assert "employee_scaling" not in memory_a.key_challenges
            logger.info("✓ User B data NOT in User A (isolation verified)")

            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("ALL TESTS PASSED ✓")
            logger.info("=" * 60)
            logger.info(f"\nUser A ({user_a.id}):")
            logger.info(f"  Industry: {memory_a.industry_focus}")
            logger.info(f"  Interests: {', '.join(memory_a.key_interests)}")
            logger.info(f"  Challenges: {', '.join(memory_a.key_challenges)}")
            logger.info(f"  Messages: {memory_a.total_messages}")
            logger.info(f"\nUser B ({user_b.id}):")
            logger.info(f"  Industry: {memory_b.industry_focus}")
            logger.info(f"  Interests: {', '.join(memory_b.key_interests)}")
            logger.info(f"  Challenges: {', '.join(memory_b.key_challenges)}")
            logger.info(f"  Messages: {memory_b.total_messages}")

            return True

        except AssertionError as e:
            logger.error(f"✗ Assertion failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def main():
    """Run all tests"""
    success = await test_multi_user_memory()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
