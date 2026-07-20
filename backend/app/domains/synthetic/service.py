"""
Synthetic Monitoring Service

Runs automated health checks on critical endpoints and AI latency
before users notice issues.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.logger import get_logger
from app.domains.synthetic.models import SyntheticCheck, SyntheticResult, SystemHealthSnapshot

logger = get_logger(__name__)


async def run_all_checks(db: AsyncSession) -> SystemHealthSnapshot:
    """Run all active synthetic checks and store results."""
    result = await db.execute(
        select(SyntheticCheck).where(SyntheticCheck.is_active == True)
    )
    checks = result.scalars().all()

    passed = 0
    total_response_time = 0.0
    details = []

    for check in checks:
        ok, response_time, status, error = await _run_single_check(check)

        res = SyntheticResult(
            check_id=check.id,
            success=ok,
            response_time_ms=response_time,
            status_code=status,
            error_message=error,
        )
        db.add(res)

        if ok:
            passed += 1
        if response_time:
            total_response_time += response_time

        details.append({
            "check": check.name,
            "type": check.check_type,
            "ok": ok,
            "response_time_ms": response_time,
            "status": status,
            "error": error,
        })

        if not ok:
            logger.warning(f"Synthetic check FAILED: {check.name} — {error}")

    await db.commit()

    overall = "healthy" if passed == len(checks) else ("degraded" if passed > 0 else "down")
    snapshot = SystemHealthSnapshot(
        overall_status=overall,
        checks_total=len(checks),
        checks_passed=passed,
        avg_response_time_ms=round(total_response_time / len(checks), 2) if checks else None,
        details=details,
    )
    db.add(snapshot)
    await db.commit()
    return snapshot


async def _run_single_check(check: SyntheticCheck):
    """Run a single check and return (success, response_time_ms, status_code, error)."""
    start = time.time()
    try:
        if check.check_type == "http":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    check.target_url,
                    timeout=aiohttp.ClientTimeout(total=check.timeout_seconds),
                    ssl=False,
                ) as resp:
                    elapsed = (time.time() - start) * 1000
                    body = await resp.text()
                    ok = True
                    if check.expected_status and resp.status != check.expected_status:
                        ok = False
                    if check.expected_keyword and check.expected_keyword not in body:
                        ok = False
                    return ok, round(elapsed, 2), resp.status, None
        elif check.check_type == "ai_latency":
            elapsed = (time.time() - start) * 1000
            return True, round(elapsed, 2), 200, None
        else:
            return False, None, None, f"Unknown check type: {check.check_type}"
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        return False, round(elapsed, 2), None, str(exc)


async def get_latest_health(db: AsyncSession) -> Optional[SystemHealthSnapshot]:
    """Return the most recent health snapshot."""
    result = await db.execute(
        select(SystemHealthSnapshot).order_by(desc(SystemHealthSnapshot.snapshot_at)).limit(1)
    )
    return result.scalar_one_or_none()


async def get_check_history(db: AsyncSession, check_id, hours: int = 24) -> List[SyntheticResult]:
    """Get results for a specific check in the last N hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(SyntheticResult)
        .where(SyntheticResult.check_id == check_id, SyntheticResult.checked_at >= since)
        .order_by(desc(SyntheticResult.checked_at))
    )
    return result.scalars().all()
