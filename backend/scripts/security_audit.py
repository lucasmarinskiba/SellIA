#!/usr/bin/env python3
"""
SellIA — Script de Auditoría de Seguridad (CLI)

Uso:
    python backend/scripts/security_audit.py

Genera un reporte de seguridad de los últimos 7 días directamente desde
la base de datos. Útil para auditorías manuales o pre-deploy.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Asegurar que el backend esté en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.domains.security.models import (
    UserLoginLog, DataAccessLog, SecretRotationLog,
    DataRetentionLog, UserSession, LoginAnomaly,
)


async def run_audit():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        day_ago = now - timedelta(days=1)

        print("=" * 60)
        print("🔐  SellIA — Security Audit Report")
        print("=" * 60)
        print(f"Generated at: {now.isoformat()}")
        print()

        # Logins
        total_logins = await db.scalar(
            select(func.count(UserLoginLog.id)).where(UserLoginLog.created_at >= week_ago)
        )
        failed_logins = await db.scalar(
            select(func.count(UserLoginLog.id)).where(
                UserLoginLog.success == False,
                UserLoginLog.created_at >= week_ago,
            )
        )
        print(f"📊  Login Activity (7d)")
        print(f"    Total logins:    {total_logins or 0}")
        print(f"    Failed logins:   {failed_logins or 0}")
        if total_logins:
            print(f"    Failure rate:    {(failed_logins/total_logins*100):.2f}%")
        print()

        # Data access
        data_access = await db.scalar(
            select(func.count(DataAccessLog.id)).where(DataAccessLog.created_at >= week_ago)
        )
        print(f"📝  Data Access Logs (7d)")
        print(f"    Total entries:   {data_access or 0}")
        print()

        # Secret rotations
        rotations = await db.scalar(
            select(func.count(SecretRotationLog.id)).where(SecretRotationLog.created_at >= week_ago)
        )
        print(f"🔄  Secret Rotations (7d)")
        print(f"    Total rotations: {rotations or 0}")
        print()

        # Data retention
        cleanups = await db.scalar(
            select(func.count(DataRetentionLog.id)).where(DataRetentionLog.started_at >= week_ago)
        )
        deleted = await db.scalar(
            select(func.coalesce(func.sum(DataRetentionLog.records_deleted), 0)).where(
                DataRetentionLog.started_at >= week_ago
            )
        )
        print(f"🗑️   Data Retention (7d)")
        print(f"    Cleanup runs:    {cleanups or 0}")
        print(f"    Records deleted: {int(deleted or 0)}")
        print()

        # Sessions
        active = await db.scalar(
            select(func.count(UserSession.id)).where(
                UserSession.is_revoked == False,
                UserSession.expires_at > now,
            )
        )
        expired = await db.scalar(
            select(func.count(UserSession.id)).where(
                UserSession.expires_at < now,
                UserSession.is_revoked == True,
            )
        )
        print(f"🔑  Sessions")
        print(f"    Active now:      {active or 0}")
        print(f"    Expired/revoked: {expired or 0}")
        print()

        # Anomalies
        anomalies = await db.scalar(
            select(func.count(LoginAnomaly.id)).where(LoginAnomaly.created_at >= week_ago)
        )
        unresolved = await db.scalar(
            select(func.count(LoginAnomaly.id)).where(
                LoginAnomaly.is_resolved == False,
            )
        )
        print(f"⚠️   Login Anomalies")
        print(f"    New (7d):        {anomalies or 0}")
        print(f"    Unresolved:      {unresolved or 0}")
        print()

        # Top countries (last 24h)
        country_result = await db.execute(
            select(UserLoginLog.country, func.count(UserLoginLog.id).label("count"))
            .where(UserLoginLog.created_at >= day_ago, UserLoginLog.country.isnot(None))
            .group_by(UserLoginLog.country)
            .order_by(func.count(UserLoginLog.id).desc())
            .limit(5)
        )
        print(f"🌍  Top Countries (24h)")
        for country, count in country_result.all():
            print(f"    {country or 'Unknown'}: {count}")
        print()

        print("=" * 60)
        print("✅  Audit complete.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_audit())
