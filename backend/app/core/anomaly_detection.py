"""
Login Anomaly Detection

Detecta logins anómalos usando z-score simple.
"""

import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.security.models import UserLoginLog, LoginAnomaly
from app.core.geo_service import haversine_distance
from app.core.logger import get_logger

logger = get_logger(__name__)


async def analyze_login_anomaly(
    db: AsyncSession,
    user_id: uuid.UUID,
    ip: str,
    country: Optional[str],
    device_fingerprint: Optional[str],
    timestamp: datetime,
) -> tuple[float, Optional[str]]:
    """
    Analiza si un login es anómalo.

    Returns:
        (anomaly_score, reason) — score 0.0 (normal) a 1.0 (anómalo)
    """
    scores = []
    reasons = []

    # 1. Velocidad imposible
    last_logins = await _get_recent_logins(db, user_id, hours=2)
    if len(last_logins) >= 2:
        # Check last two logins
        ll1, ll2 = last_logins[:2]
        if ll1.latitude and ll1.longitude and ll2.latitude and ll2.longitude:
            dist_km = haversine_distance(
                ll1.latitude, ll1.longitude,
                ll2.latitude, ll2.longitude,
            )
            time_diff_hours = (ll2.created_at - ll1.created_at).total_seconds() / 3600
            if time_diff_hours > 0:
                speed_kmh = dist_km / time_diff_hours
                if speed_kmh > 800:  # Imposible viajar > 800 km/h
                    scores.append(0.95)
                    reasons.append(f"Velocidad imposible: {speed_kmh:.0f} km/h desde {ll1.country} a {ll2.country}")

    # 2. Horario inusual
    hour_score = await _check_unusual_hour(db, user_id, timestamp)
    if hour_score > 0.7:
        scores.append(hour_score)
        reasons.append(f"Horario inusual: {timestamp.hour}:00")

    # 3. País nuevo
    last_countries = {ll.country for ll in last_logins if ll.country}
    if country and country not in last_countries and len(last_countries) > 0:
        scores.append(0.6)
        reasons.append(f"Login desde país nuevo: {country}")

    # 4. Múltiples dispositivos
    recent_devices = {ll.device_fingerprint for ll in last_logins if ll.device_fingerprint}
    if device_fingerprint and device_fingerprint not in recent_devices and len(recent_devices) >= 2:
        scores.append(0.5)
        reasons.append("Nuevo dispositivo en sesión reciente")

    if not scores:
        return 0.0, None

    # Weighted average
    max_score = max(scores)
    reason = reasons[scores.index(max_score)]
    return min(max_score, 1.0), reason


async def _get_recent_logins(db: AsyncSession, user_id: uuid.UUID, hours: int = 2):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(UserLoginLog).where(
            UserLoginLog.user_id == user_id,
            UserLoginLog.success == True,
            UserLoginLog.created_at >= since,
        ).order_by(UserLoginLog.created_at.desc())
    )
    return list(result.scalars().all())


async def _check_unusual_hour(db: AsyncSession, user_id: uuid.UUID, timestamp: datetime) -> float:
    """Detecta si el horario de login es inusual para el usuario."""
    # Get user's typical login hours (last 30 days)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(func.extract('hour', UserLoginLog.created_at))
        .where(
            UserLoginLog.user_id == user_id,
            UserLoginLog.success == True,
            UserLoginLog.created_at >= since,
        )
    )
    hours = [h[0] for h in result.all()]
    if len(hours) < 5:
        return 0.0  # Not enough data

    current_hour = timestamp.hour
    mean_hour = sum(hours) / len(hours)
    std_dev = math.sqrt(sum((h - mean_hour) ** 2 for h in hours) / len(hours)) or 1

    z_score = abs(current_hour - mean_hour) / std_dev
    score = min(0.9, z_score / 3)  # Normalize
    return score


async def record_anomaly(
    db: AsyncSession,
    user_id: uuid.UUID,
    anomaly_type: str,
    description: str,
    score: float,
    ip: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    country: Optional[str] = None,
) -> LoginAnomaly:
    """Registra una anomalía detectada."""
    anomaly = LoginAnomaly(
        user_id=user_id,
        anomaly_type=anomaly_type,
        description=description,
        score=score,
        ip_address=ip,
        device_fingerprint=device_fingerprint,
        country=country,
    )
    db.add(anomaly)
    await db.commit()
    await db.refresh(anomaly)

    logger.warning(f"Login anomaly detected for user {user_id}: {anomaly_type} (score {score:.2f})")
    return anomaly
