"""Prometheus-style /metrics endpoint · scrape by Grafana/Datadog."""
import os
import time
from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import func, select

from app.db.models import AuditLog, Deal, Tenant, User
from app.db.session import AsyncSessionLocal


router = APIRouter()

START_TIME = time.time()


@router.get("", response_class=Response)
async def metrics() -> Response:
    """Plaintext metrics in Prometheus exposition format."""
    lines: list[str] = []

    # Process info
    lines.append("# HELP sellia_uptime_seconds Process uptime")
    lines.append("# TYPE sellia_uptime_seconds counter")
    lines.append(f"sellia_uptime_seconds {time.time() - START_TIME:.0f}")

    # Aggregate DB stats · runs as superuser query (no RLS bind)
    try:
        async with AsyncSessionLocal() as db:
            tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar() or 0
            users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
            deals = (await db.execute(select(func.count()).select_from(Deal))).scalar() or 0
            audits = (await db.execute(select(func.count()).select_from(AuditLog))).scalar() or 0

            # By plan
            plans_q = await db.execute(select(Tenant.plan, func.count()).group_by(Tenant.plan))
            plans = dict(plans_q.all())

            # By stage
            stages_q = await db.execute(select(Deal.stage, func.count()).group_by(Deal.stage))
            stages = {str(s): c for s, c in stages_q.all()}
    except Exception:
        tenants = users = deals = audits = 0
        plans = {}
        stages = {}

    lines.append("\n# HELP sellia_tenants_total Total tenants")
    lines.append("# TYPE sellia_tenants_total gauge")
    lines.append(f"sellia_tenants_total {tenants}")

    lines.append("\n# HELP sellia_users_total Total users")
    lines.append("# TYPE sellia_users_total gauge")
    lines.append(f"sellia_users_total {users}")

    lines.append("\n# HELP sellia_deals_total Total deals")
    lines.append("# TYPE sellia_deals_total gauge")
    lines.append(f"sellia_deals_total {deals}")

    lines.append("\n# HELP sellia_audit_logs_total Total audit log entries")
    lines.append("# TYPE sellia_audit_logs_total counter")
    lines.append(f"sellia_audit_logs_total {audits}")

    if plans:
        lines.append("\n# HELP sellia_tenants_by_plan Tenants by plan")
        lines.append("# TYPE sellia_tenants_by_plan gauge")
        for plan, count in plans.items():
            lines.append(f'sellia_tenants_by_plan{{plan="{plan}"}} {count}')

    if stages:
        lines.append("\n# HELP sellia_deals_by_stage Deals by stage")
        lines.append("# TYPE sellia_deals_by_stage gauge")
        for stage, count in stages.items():
            lines.append(f'sellia_deals_by_stage{{stage="{stage}"}} {count}')

    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
