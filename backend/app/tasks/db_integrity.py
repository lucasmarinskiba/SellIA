"""Database integrity checker for orphaned records and data consistency."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IntegrityCheckResult:
    def __init__(self, name: str, passed: bool, details: list[dict[str, Any]] | None = None):
        self.name = name
        self.passed = passed
        self.details = details or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "count": len(self.details),
            "details": self.details[:50],  # limit details
        }


async def check_orphaned_messages(db: AsyncSession) -> IntegrityCheckResult:
    """Messages without a valid conversation."""
    query = text("""
        SELECT m.id, m.conversation_id
        FROM messages m
        LEFT JOIN conversations c ON m.conversation_id = c.id
        WHERE c.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"message_id": str(r["id"]), "conversation_id": str(r["conversation_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_messages", len(details) == 0, details)


async def check_orphaned_orders(db: AsyncSession) -> IntegrityCheckResult:
    """Orders without a valid business."""
    query = text("""
        SELECT o.id, o.business_id
        FROM orders o
        LEFT JOIN businesses b ON o.business_id = b.id
        WHERE b.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"order_id": str(r["id"]), "business_id": str(r["business_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_orders", len(details) == 0, details)


async def check_orphaned_catalog_items(db: AsyncSession) -> IntegrityCheckResult:
    """Catalog items without a valid business."""
    query = text("""
        SELECT ci.id, ci.business_id
        FROM catalog_items ci
        LEFT JOIN businesses b ON ci.business_id = b.id
        WHERE b.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"item_id": str(r["id"]), "business_id": str(r["business_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_catalog_items", len(details) == 0, details)


async def check_orphaned_workflow_executions(db: AsyncSession) -> IntegrityCheckResult:
    """Workflow executions without a valid workflow."""
    query = text("""
        SELECT we.id, we.workflow_id
        FROM workflow_executions we
        LEFT JOIN workflows w ON we.workflow_id = w.id
        WHERE w.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"execution_id": str(r["id"]), "workflow_id": str(r["workflow_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_workflow_executions", len(details) == 0, details)


async def check_orphaned_agent_conversations(db: AsyncSession) -> IntegrityCheckResult:
    """Agent conversations without a valid agent."""
    query = text("""
        SELECT ac.id, ac.agent_id
        FROM agent_conversations ac
        LEFT JOIN agents a ON ac.agent_id = a.id
        WHERE a.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"conversation_id": str(r["id"]), "agent_id": str(r["agent_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_agent_conversations", len(details) == 0, details)


async def check_orphaned_revenue_events(db: AsyncSession) -> IntegrityCheckResult:
    """Revenue events without a valid order."""
    query = text("""
        SELECT re.id, re.order_id
        FROM revenue_events re
        LEFT JOIN orders o ON re.order_id = o.id
        WHERE o.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"event_id": str(r["id"]), "order_id": str(r["order_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_revenue_events", len(details) == 0, details)


async def check_orphaned_deals(db: AsyncSession) -> IntegrityCheckResult:
    """Deals without a valid business."""
    query = text("""
        SELECT d.id, d.business_id
        FROM deals d
        LEFT JOIN businesses b ON d.business_id = b.id
        WHERE b.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"deal_id": str(r["id"]), "business_id": str(r["business_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_deals", len(details) == 0, details)


async def check_orphaned_subscriptions(db: AsyncSession) -> IntegrityCheckResult:
    """Subscriptions without a valid user."""
    query = text("""
        SELECT s.id, s.user_id
        FROM subscriptions s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE u.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"subscription_id": str(r["id"]), "user_id": str(r["user_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_subscriptions", len(details) == 0, details)


async def check_orphaned_business_users(db: AsyncSession) -> IntegrityCheckResult:
    """BusinessUserRole records without valid user or business."""
    query = text("""
        SELECT bur.id, bur.user_id, bur.business_id
        FROM business_user_roles bur
        LEFT JOIN users u ON bur.user_id = u.id
        LEFT JOIN businesses b ON bur.business_id = b.id
        WHERE u.id IS NULL OR b.id IS NULL
        LIMIT 1000
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"role_id": str(r["id"]), "user_id": str(r["user_id"]), "business_id": str(r["business_id"])} for r in rows]
    return IntegrityCheckResult("orphaned_business_user_roles", len(details) == 0, details)


async def check_duplicate_idempotency_keys(db: AsyncSession) -> IntegrityCheckResult:
    """Idempotency keys with duplicate key values (should not happen due to unique index)."""
    query = text("""
        SELECT key, COUNT(*) as cnt
        FROM idempotency_keys
        GROUP BY key
        HAVING COUNT(*) > 1
        LIMIT 100
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"key": r["key"], "count": r["cnt"]} for r in rows]
    return IntegrityCheckResult("duplicate_idempotency_keys", len(details) == 0, details)


async def check_duplicate_webhook_events(db: AsyncSession) -> IntegrityCheckResult:
    """Webhook event logs with duplicate provider+event_id (should not happen due to unique index)."""
    query = text("""
        SELECT provider, event_id, COUNT(*) as cnt
        FROM webhook_event_logs
        GROUP BY provider, event_id
        HAVING COUNT(*) > 1
        LIMIT 100
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"provider": r["provider"], "event_id": r["event_id"], "count": r["cnt"]} for r in rows]
    return IntegrityCheckResult("duplicate_webhook_events", len(details) == 0, details)


async def check_negative_amounts(db: AsyncSession) -> IntegrityCheckResult:
    """Orders or revenue events with negative amounts."""
    query = text("""
        SELECT id, total_amount, business_id
        FROM orders
        WHERE total_amount < 0
        LIMIT 100
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    details = [{"order_id": str(r["id"]), "total_amount": float(r["total_amount"]), "business_id": str(r["business_id"])} for r in rows]
    return IntegrityCheckResult("negative_order_amounts", len(details) == 0, details)


ALL_CHECKS = [
    check_orphaned_messages,
    check_orphaned_orders,
    check_orphaned_catalog_items,
    check_orphaned_workflow_executions,
    check_orphaned_agent_conversations,
    check_orphaned_revenue_events,
    check_orphaned_deals,
    check_orphaned_subscriptions,
    check_orphaned_business_users,
    check_duplicate_idempotency_keys,
    check_duplicate_webhook_events,
    check_negative_amounts,
]


async def run_all_integrity_checks(db: AsyncSession) -> dict[str, Any]:
    """Run all integrity checks and return a summary report."""
    results = []
    passed = 0
    failed = 0

    for check in ALL_CHECKS:
        try:
            result = await check(db)
            results.append(result.to_dict())
            if result.passed:
                passed += 1
            else:
                failed += 1
                logger.warning("Integrity check failed: %s (%d issues)", result.name, len(result.details))
        except Exception as e:
            logger.exception("Integrity check error: %s", check.__name__)
            results.append({"name": check.__name__, "passed": False, "error": str(e)})
            failed += 1

    summary = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": len(ALL_CHECKS),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    if failed > 0:
        logger.error("DB integrity check completed: %d/%d checks failed", failed, len(ALL_CHECKS))
    else:
        logger.info("DB integrity check completed: all %d checks passed", len(ALL_CHECKS))

    return summary
