"""Security & Compliance Celery Tasks.

Data retention, secret rotation, and cleanup.
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from celery import shared_task
from sqlalchemy import select, text, func

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.channels.models import ChannelConnection
from app.domains.security.models import (
    UserLoginLog,
    DataAccessLog,
    DataRetentionPolicy,
    DataRetentionLog,
    SecretRotationLog,
    UserSession,
    SecurityWebhook,
    BlockedIP,
)

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Data Retention Cleanup
# ---------------------------------------------------------------------------

DEFAULT_HARD_RETENTION = {
    "user_login_logs": 365,
    "data_access_logs": 180,
    "conversations": 730,
    "messages": 730,
    "orders": 1095,
    "sales_invoices": 1095,
    "payment_reminders": 365,
    "user_sessions": 90,
    "email_otps": 30,
    "breach_check_logs": 180,
}

# Tables that support business-scoped deletion (have business_id column)
BUSINESS_SCOPED_TABLES = {
    "conversations",
    "orders",
    "sales_invoices",
    "payment_reminders",
    "data_access_logs",
}


@shared_task(name="app.tasks.security_tasks.data_retention_cleanup")
def data_retention_cleanup():
    """Delete old data according to retention policies (configurable + hard defaults)."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            total_deleted = {}

            # 1. Load active retention policies
            result = await db.execute(
                select(DataRetentionPolicy).where(DataRetentionPolicy.is_active == True)
            )
            policies = result.scalars().all()

            # Build effective retention map: table_name -> retention_days
            # Policies without business_id are global; per-business policies override
            effective = dict(DEFAULT_HARD_RETENTION)
            for policy in policies:
                key = f"{policy.table_name}:{policy.business_id}" if policy.business_id else policy.table_name
                effective[key] = policy.retention_days

            # 2. Execute deletions per default table
            tables_to_clean = list(DEFAULT_HARD_RETENTION.keys())
            # Add any extra tables from policies
            for policy in policies:
                if policy.table_name not in tables_to_clean:
                    tables_to_clean.append(policy.table_name)

            for tbl in tables_to_clean:
                log_entry = DataRetentionLog(
                    table_name=tbl,
                    records_deleted=0,
                    status="success",
                )
                db.add(log_entry)

                try:
                    retention_days = effective.get(tbl, effective.get(f"{tbl}:None", DEFAULT_HARD_RETENTION.get(tbl, 365)))
                    cutoff = now - timedelta(days=retention_days)

                    if tbl == "user_login_logs":
                        res = await db.execute(
                            UserLoginLog.__table__.delete().where(
                                UserLoginLog.created_at < cutoff
                            )
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "data_access_logs":
                        res = await db.execute(
                            DataAccessLog.__table__.delete().where(
                                DataAccessLog.created_at < cutoff
                            )
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "conversations":
                        # Conversations has business_id — we can scope by policy
                        for policy in policies:
                            if policy.table_name == tbl and policy.business_id:
                                p_cutoff = now - timedelta(days=policy.retention_days)
                                res = await db.execute(
                                    text(
                                        "DELETE FROM conversations WHERE business_id = :bid AND created_at < :cutoff AND status = 'archived'"
                                    ),
                                    {"bid": str(policy.business_id), "cutoff": p_cutoff},
                                )
                                total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                                log_entry.records_deleted += res.rowcount
                                log_entry.policy_id = policy.id
                        # Fallback global cleanup
                        global_cutoff = now - timedelta(days=effective.get(tbl, DEFAULT_HARD_RETENTION.get(tbl, 730)))
                        res = await db.execute(
                            text(
                                "DELETE FROM conversations WHERE created_at < :cutoff AND status = 'archived'"
                            ),
                            {"cutoff": global_cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted += res.rowcount

                    elif tbl == "messages":
                        # Messages have no business_id; delete orphaned messages older than cutoff
                        res = await db.execute(
                            text(
                                "DELETE FROM messages WHERE created_at < :cutoff AND conversation_id NOT IN (SELECT id FROM conversations)"
                            ),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "orders":
                        res = await db.execute(
                            text(
                                "DELETE FROM orders WHERE created_at < :cutoff AND status IN ('cancelled', 'refunded')"
                            ),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "sales_invoices":
                        res = await db.execute(
                            text(
                                "DELETE FROM sales_invoices WHERE created_at < :cutoff AND status = 'cancelled'"
                            ),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "payment_reminders":
                        res = await db.execute(
                            text(
                                "DELETE FROM payment_reminders WHERE created_at < :cutoff AND sent_at IS NOT NULL"
                            ),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "user_sessions":
                        res = await db.execute(
                            UserSession.__table__.delete().where(
                                UserSession.expires_at < now
                            )
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "email_otps":
                        res = await db.execute(
                            text("DELETE FROM email_otps WHERE created_at < :cutoff AND is_used = TRUE"),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    elif tbl == "breach_check_logs":
                        res = await db.execute(
                            text("DELETE FROM breach_check_logs WHERE checked_at < :cutoff"),
                            {"cutoff": cutoff},
                        )
                        total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                        log_entry.records_deleted = res.rowcount

                    else:
                        # Generic DELETE for any other table with created_at
                        try:
                            res = await db.execute(
                                text(f"DELETE FROM {tbl} WHERE created_at < :cutoff"),
                                {"cutoff": cutoff},
                            )
                            total_deleted[tbl] = total_deleted.get(tbl, 0) + res.rowcount
                            log_entry.records_deleted = res.rowcount
                        except Exception as e:
                            logger.warning(f"Generic cleanup failed for {tbl}: {e}")
                            log_entry.status = "error"
                            log_entry.error_message = str(e)[:500]

                except Exception as e:
                    logger.error(f"Data retention cleanup error for {tbl}: {e}")
                    log_entry.status = "error"
                    log_entry.error_message = str(e)[:500]

                log_entry.completed_at = datetime.now(timezone.utc)

            await db.commit()
            logger.info(f"Data retention cleanup completed: {total_deleted}")
            return total_deleted

    return _async_run(_run())


# ---------------------------------------------------------------------------
# Webhook Token Rotation
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.rotate_webhook_tokens")
def rotate_webhook_tokens():
    """Rotate webhook tokens for active channels older than 90 days."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=90)

            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.created_at < cutoff,
                    ChannelConnection.is_active == True,
                )
            )
            channels = result.scalars().all()
            rotated = 0
            errors = 0

            for ch in channels:
                old_token = ch.webhook_token or ""
                old_hash = hashlib.sha256(old_token.encode()).hexdigest()[:16] if old_token else None
                new_token = secrets.token_urlsafe(32)
                new_hash = hashlib.sha256(new_token.encode()).hexdigest()[:16]

                log = SecretRotationLog(
                    business_id=ch.business_id,
                    secret_type="webhook_token",
                    target_id=str(ch.id),
                    old_value_hash=old_hash,
                    new_value_hash=new_hash,
                    status="success",
                )
                db.add(log)

                try:
                    ch.webhook_token = new_token
                    rotated += 1
                except Exception as e:
                    logger.error(f"Failed to rotate webhook token for channel {ch.id}: {e}")
                    log.status = "error"
                    log.error_message = str(e)[:500]
                    errors += 1

            await db.commit()
            logger.info(f"Rotated {rotated} webhook tokens ({errors} errors)")
            return {"rotated": rotated, "errors": errors}

    return _async_run(_run())


# ---------------------------------------------------------------------------
# Expired Secrets Rotation / Cleanup
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.rotate_expired_secrets")
def rotate_expired_secrets():
    """Rotate expired secrets: security webhook secrets, and clean up stale sessions."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            total = {"webhook_secrets": 0, "sessions_cleaned": 0, "errors": 0}

            # 1. Rotate SecurityWebhook secrets older than 180 days
            cutoff_webhook = now - timedelta(days=180)
            result = await db.execute(
                select(SecurityWebhook).where(
                    SecurityWebhook.created_at < cutoff_webhook,
                    SecurityWebhook.is_active == True,
                    SecurityWebhook.secret.isnot(None),
                )
            )
            webhooks = result.scalars().all()
            for wh in webhooks:
                old_secret = wh.secret or ""
                old_hash = hashlib.sha256(old_secret.encode()).hexdigest()[:16] if old_secret else None
                new_secret = secrets.token_urlsafe(32)
                new_hash = hashlib.sha256(new_secret.encode()).hexdigest()[:16]

                log = SecretRotationLog(
                    secret_type="security_webhook_secret",
                    target_id=str(wh.id),
                    old_value_hash=old_hash,
                    new_value_hash=new_hash,
                    status="success",
                )
                db.add(log)
                try:
                    wh.secret = new_secret
                    total["webhook_secrets"] += 1
                except Exception as e:
                    logger.error(f"Failed to rotate security webhook secret {wh.id}: {e}")
                    log.status = "error"
                    log.error_message = str(e)[:500]
                    total["errors"] += 1

            # 2. Clean up expired user sessions
            try:
                res = await db.execute(
                    UserSession.__table__.delete().where(
                        UserSession.expires_at < now,
                        UserSession.is_revoked == True,
                    )
                )
                total["sessions_cleaned"] = res.rowcount
            except Exception as e:
                logger.error(f"Failed to clean expired sessions: {e}")
                total["errors"] += 1

            await db.commit()
            logger.info(f"Expired secrets rotation completed: {total}")
            return total

    return _async_run(_run())


# ---------------------------------------------------------------------------
# Weekly Security Audit Report
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.security_audit_report")
def security_audit_report():
    """Generate and dispatch a weekly security audit summary."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            week_ago = now - timedelta(days=7)

            # Login stats
            total_logins = await db.scalar(
                select(func.count(UserLoginLog.id)).where(
                    UserLoginLog.created_at >= week_ago
                )
            )
            failed_logins = await db.scalar(
                select(func.count(UserLoginLog.id)).where(
                    UserLoginLog.success == False,
                    UserLoginLog.created_at >= week_ago,
                )
            )

            # Data access logs
            data_access_count = await db.scalar(
                select(func.count(DataAccessLog.id)).where(
                    DataAccessLog.created_at >= week_ago
                )
            )

            # Secret rotations
            rotations = await db.scalar(
                select(func.count(SecretRotationLog.id)).where(
                    SecretRotationLog.created_at >= week_ago
                )
            )

            # Data retention cleanups
            cleanups = await db.scalar(
                select(func.count(DataRetentionLog.id)).where(
                    DataRetentionLog.started_at >= week_ago
                )
            )
            records_deleted = await db.scalar(
                select(func.coalesce(func.sum(DataRetentionLog.records_deleted), 0)).where(
                    DataRetentionLog.started_at >= week_ago
                )
            )

            # Active sessions
            active_sessions = await db.scalar(
                select(func.count(UserSession.id)).where(
                    UserSession.is_revoked == False,
                    UserSession.expires_at > now,
                )
            )

            report = {
                "period": f"{week_ago.isoformat()} to {now.isoformat()}",
                "total_logins_7d": total_logins or 0,
                "failed_logins_7d": failed_logins or 0,
                "failed_rate_pct": round((failed_logins / total_logins * 100), 2) if total_logins else 0.0,
                "data_access_logs_7d": data_access_count or 0,
                "secret_rotations_7d": rotations or 0,
                "data_retention_cleanups_7d": cleanups or 0,
                "records_deleted_7d": int(records_deleted or 0),
                "active_sessions_now": active_sessions or 0,
            }

            logger.info(f"Weekly security audit report: {report}")

            # Dispatch to security webhooks (Slack/Discord/Telegram)
            webhooks = await db.execute(
                select(SecurityWebhook).where(SecurityWebhook.is_active == True)
            )
            for wh in webhooks.scalars().all():
                try:
                    import aiohttp
                    payload = {
                        "text": (
                            f"🔐 *SellIA Security Report* ({report['period']})\n"
                            f"• Logins: {report['total_logins_7d']} (failed: {report['failed_logins_7d']})\n"
                            f"• Data access logs: {report['data_access_logs_7d']}\n"
                            f"• Secret rotations: {report['secret_rotations_7d']}\n"
                            f"• Records deleted (retention): {report['records_deleted_7d']}\n"
                            f"• Active sessions: {report['active_sessions_now']}"
                        )
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(wh.url, json=payload) as resp:
                            if resp.status >= 400:
                                logger.warning(f"Webhook {wh.id} returned {resp.status}")
                except Exception as e:
                    logger.warning(f"Failed to send audit report to webhook {wh.id}: {e}")

            return report

    return _async_run(_run())


# ---------------------------------------------------------------------------
# Auto IP Blocklist Cleanup
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.cleanup_expired_ip_blocks")
def cleanup_expired_ip_blocks():
    """Elimina bloqueos de IP que ya expiraron."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                BlockedIP.__table__.delete().where(
                    BlockedIP.blocked_until.isnot(None),
                    BlockedIP.blocked_until < now,
                )
            )
            await db.commit()
            logger.info(f"Cleaned up {result.rowcount} expired IP blocks")
            return {"cleaned": result.rowcount}

    return _async_run(_run())


# ---------------------------------------------------------------------------
# Auto Block High-Risk IPs (audacia)
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.auto_block_high_risk_ips")
def auto_block_high_risk_ips():
    """Bloquea automáticamente IPs con múltiples logins fallidos recientes."""

    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)

            # IPs con 5+ logins fallidos en la última hora
            result = await db.execute(
                select(
                    UserLoginLog.ip_address,
                    func.count(UserLoginLog.id).label("fail_count"),
                )
                .where(
                    UserLoginLog.success == False,
                    UserLoginLog.created_at >= hour_ago,
                )
                .group_by(UserLoginLog.ip_address)
                .having(func.count(UserLoginLog.id) >= 5)
            )
            blocked = 0
            for ip_address, fail_count in result.all():
                if not ip_address:
                    continue
                # Verificar si ya está bloqueada
                existing = await db.execute(
                    select(BlockedIP).where(BlockedIP.ip_address == ip_address)
                )
                if existing.scalar_one_or_none():
                    continue

                block = BlockedIP(
                    ip_address=ip_address,
                    reason="brute_force",
                    blocked_until=now + timedelta(hours=24),
                )
                db.add(block)
                blocked += 1
                logger.warning(f"Auto-blocked IP {ip_address} after {fail_count} failed logins")

            await db.commit()
            return {"blocked": blocked}

    return _async_run(_run())


# ---------------------------------------------------------------------------
# DB Integrity Check
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.security_tasks.db_integrity_check")
def db_integrity_check():
    """Run database integrity checks weekly."""
    from app.tasks.db_integrity import run_all_integrity_checks

    async def _run():
        async with AsyncSessionLocal() as db:
            report = await run_all_integrity_checks(db)
            # Log summary
            if report["failed"] > 0:
                logger.error("DB integrity check: %d/%d failed", report["failed"], report["total"])
            else:
                logger.info("DB integrity check: all %d checks passed", report["total"])
            return report

    return _async_run(_run())
