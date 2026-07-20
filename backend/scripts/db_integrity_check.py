#!/usr/bin/env python3
"""
SellIA — Database Integrity Checker

Valida integridad referencial y consistencia de datos.
Uso:
    python backend/scripts/db_integrity_check.py [--repair]
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timezone
from sqlalchemy import select, text

sys.path.insert(0, "backend")

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger

logger = get_logger(__name__)


async def run_checks(repair: bool = False) -> dict:
    async with AsyncSessionLocal() as db:
        report = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "issues": [],
            "summary": {"total_issues": 0, "repaired": 0},
        }

        # 1. Orphaned messages (no conversation)
        res = await db.execute(
            text("SELECT COUNT(*) FROM messages WHERE conversation_id NOT IN (SELECT id FROM conversations)")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "orphaned_messages", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(
                    text("DELETE FROM messages WHERE conversation_id NOT IN (SELECT id FROM conversations)")
                )
                report["summary"]["repaired"] += count

        # 2. Orphaned orders (no business)
        res = await db.execute(
            text("SELECT COUNT(*) FROM orders WHERE business_id NOT IN (SELECT id FROM businesses)")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "orphaned_orders", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(text("DELETE FROM orders WHERE business_id NOT IN (SELECT id FROM businesses)"))
                report["summary"]["repaired"] += count

        # 3. Orphaned sales_invoices (no business)
        res = await db.execute(
            text("SELECT COUNT(*) FROM sales_invoices WHERE business_id NOT IN (SELECT id FROM businesses)")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "orphaned_sales_invoices", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(
                    text("DELETE FROM sales_invoices WHERE business_id NOT IN (SELECT id FROM businesses)")
                )
                report["summary"]["repaired"] += count

        # 4. Expired sessions not revoked
        res = await db.execute(
            text("SELECT COUNT(*) FROM user_sessions WHERE expires_at < NOW() AND is_revoked = FALSE")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "expired_sessions_not_revoked", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(
                    text("UPDATE user_sessions SET is_revoked = TRUE WHERE expires_at < NOW() AND is_revoked = FALSE")
                )
                report["summary"]["repaired"] += count

        # 5. Duplicate webhook_token (should be unique but let's verify)
        res = await db.execute(
            text("SELECT webhook_token, COUNT(*) FROM channel_connections GROUP BY webhook_token HAVING COUNT(*) > 1")
        )
        dups = res.all()
        if dups:
            report["issues"].append({"category": "duplicate_webhook_tokens", "count": len(dups), "tokens": [r[0] for r in dups]})
            report["summary"]["total_issues"] += len(dups)

        # 6. Orphaned revenue_events (no order)
        res = await db.execute(
            text("SELECT COUNT(*) FROM revenue_events WHERE order_id NOT IN (SELECT id FROM orders)")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "orphaned_revenue_events", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(
                    text("DELETE FROM revenue_events WHERE order_id NOT IN (SELECT id FROM orders)")
                )
                report["summary"]["repaired"] += count

        # 7. Orphaned workflow_executions (no workflow)
        res = await db.execute(
            text("SELECT COUNT(*) FROM workflow_executions WHERE workflow_id NOT IN (SELECT id FROM workflows)")
        )
        count = res.scalar()
        if count:
            report["issues"].append({"category": "orphaned_workflow_executions", "count": count})
            report["summary"]["total_issues"] += count
            if repair:
                await db.execute(
                    text("DELETE FROM workflow_executions WHERE workflow_id NOT IN (SELECT id FROM workflows)")
                )
                report["summary"]["repaired"] += count

        if repair:
            await db.commit()

        return report


def main():
    parser = argparse.ArgumentParser(description="SellIA DB Integrity Checker")
    parser.add_argument("--repair", action="store_true", help="Auto-repair issues where safe")
    args = parser.parse_args()

    report = asyncio.run(run_checks(repair=args.repair))
    print(json.dumps(report, indent=2))

    if report["summary"]["total_issues"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
