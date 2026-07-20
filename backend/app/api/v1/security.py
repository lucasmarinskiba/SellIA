"""
Endpoints de gestión de seguridad:
- Webhooks de alertas
- Configuración global de seguridad (bloqueo por país, etc.)
- Logs de login
- Push notifications (Web Push)
- Sesiones activas (ver y revocar)
- Admin audit logs
"""

import hashlib
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.push_notifications import get_vapid_public_key, send_security_push
from app.core.hibp_service import check_email_breaches, format_breach_alert
from app.domains.users.models import User
from app.domains.security.models import (
    SecurityWebhook, SecurityConfig, UserLoginLog, PushSubscription, UserSession,
    TwoFABackupCode, BreachCheckLog, DataAccessLog, SecretRotationLog,
    DataRetentionLog, DataRetentionPolicy,
)
from app.domains.security.schemas import (
    SecurityWebhookCreate,
    SecurityWebhookResponse,
    SecurityConfigUpdate,
    SecurityConfigResponse,
    LoginLogResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    UserSessionResponse,
    AuditLogResponse,
    SecurityStatsResponse,
    BackupCodeResponse,
    BreachCheckResponse,
)

router = APIRouter()


# ===== Webhooks =====

@router.post("/webhooks", response_model=SecurityWebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: SecurityWebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    webhook = SecurityWebhook(**data.model_dump())
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.get("/webhooks", response_model=List[SecurityWebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    result = await db.execute(select(SecurityWebhook))
    return result.scalars().all()


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    result = await db.execute(select(SecurityWebhook).where(SecurityWebhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")

    await db.delete(webhook)
    await db.commit()
    return {"detail": "Webhook eliminado"}


# ===== Configuración global =====

@router.get("/config", response_model=SecurityConfigResponse)
async def get_security_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    result = await db.execute(select(SecurityConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SecurityConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.put("/config", response_model=SecurityConfigResponse)
async def update_security_config(
    data: SecurityConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    result = await db.execute(select(SecurityConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SecurityConfig(**data.model_dump(exclude_unset=True))
        db.add(config)
    else:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config


# ===== Login logs (propios) =====

@router.get("/login-logs", response_model=List[LoginLogResponse])
async def get_my_login_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(UserLoginLog)
        .where(UserLoginLog.user_id == current_user.id)
        .order_by(UserLoginLog.created_at.desc())
    )
    return result.scalars().all()


# ===== Push Notifications =====

@router.get("/push/vapid-public-key")
async def get_vapid_key():
    key = get_vapid_public_key()
    if not key:
        raise HTTPException(status_code=500, detail="VAPID no configurado")
    return {"public_key": key}


@router.post("/push/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_push(
    data: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == data.endpoint,
            PushSubscription.user_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.is_active = True
        existing.p256dh = data.p256dh
        existing.auth = data.auth
        existing.user_agent = data.user_agent
        await db.commit()
        await db.refresh(existing)
        return existing

    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth,
        user_agent=data.user_agent,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/push/unsubscribe")
async def unsubscribe_push(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.is_active = False
        await db.commit()
    return {"detail": "Suscripción desactivada"}


@router.post("/push/test")
async def test_push(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await send_security_push(
            db=db,
            user_id=str(current_user.id),
            event="test",
            title="🧪 Notificación de prueba",
            body="¡Las notificaciones push están funcionando correctamente en SellIA!",
        )
        return {"detail": "Notificación de prueba enviada"}
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error sending push notification")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===== Sesiones activas =====

@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_my_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")

    current_session_hash = None
    if token:
        current_session_hash = hashlib.sha256(token.encode()).hexdigest()[:64]

    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(UserSession.last_active_at.desc())
    )
    sessions = result.scalars().all()

    response_sessions = []
    for sess in sessions:
        data = {
            "id": str(sess.id),
            "device_name": sess.device_name,
            "device_fingerprint": sess.device_fingerprint,
            "ip_address": sess.ip_address,
            "user_agent": sess.user_agent,
            "country": sess.country,
            "last_active_at": sess.last_active_at,
            "expires_at": sess.expires_at,
            "is_revoked": sess.is_revoked,
            "created_at": sess.created_at,
            "is_current": sess.session_token == current_session_hash,
        }
        response_sessions.append(data)

    return response_sessions


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    session.is_revoked = True
    await db.commit()

    try:
        await send_security_push(
            db=db,
            user_id=str(current_user.id),
            event="session_revoked",
            title="🔒 Sesión cerrada remotamente",
            body=f"Se cerró una sesión en {session.device_name or 'un dispositivo'}. Si no fuiste vos, cambiá tu contraseña.",
        )
    except Exception:
        pass

    return {"detail": "Sesión revocada correctamente"}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")

    current_session_hash = None
    if token:
        current_session_hash = hashlib.sha256(token.encode()).hexdigest()[:64]

    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    sessions = result.scalars().all()
    revoked_count = 0

    for sess in sessions:
        if sess.session_token != current_session_hash:
            sess.is_revoked = True
            revoked_count += 1

    await db.commit()
    return {"detail": f"{revoked_count} sesiones revocadas"}


# ===== Admin Audit Logs =====

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),  # success, failed
    ip: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Panel de auditoría: ver todos los logs de todos los usuarios (solo admin)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    query = select(UserLoginLog, User.email).join(User, UserLoginLog.user_id == User.id)

    if user_id:
        query = query.where(UserLoginLog.user_id == user_id)
    if event_type == "success":
        query = query.where(UserLoginLog.success == True)
    elif event_type == "failed":
        query = query.where(UserLoginLog.success == False)
    if ip:
        query = query.where(UserLoginLog.ip_address.ilike(f"%{ip}%"))
    if country:
        query = query.where(UserLoginLog.country.ilike(f"%{country}%"))
    if date_from:
        query = query.where(UserLoginLog.created_at >= date_from)
    if date_to:
        query = query.where(UserLoginLog.created_at <= date_to)

    query = query.order_by(UserLoginLog.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    logs = []
    for log, email in rows:
        logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "country": log.country,
            "city": log.city,
            "success": log.success,
            "created_at": log.created_at,
        })

    return logs


@router.get("/audit-stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Estadísticas de seguridad del día (solo admin)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total logins hoy
    total_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == True,
            UserLoginLog.created_at >= today_start,
        )
    )

    # Logins fallidos hoy
    failed_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == False,
            UserLoginLog.created_at >= today_start,
        )
    )

    # Nuevos dispositivos hoy (simplificado: logins con distintos fingerprints)
    new_devices = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == True,
            UserLoginLog.created_at >= today_start,
        )
    )  # Simplificado

    # Sesiones activas
    active_sessions = await db.scalar(
        select(func.count(UserSession.id)).where(
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    # Bloqueos por país hoy
    blocked = 0  # Requiere tracking adicional

    # Violaciones de geofencing hoy
    geofence_violations = 0  # Requiere tracking adicional

    return {
        "total_logins_today": total_logins or 0,
        "failed_logins_today": failed_logins or 0,
        "new_devices_today": new_devices or 0,
        "active_sessions": active_sessions or 0,
        "blocked_attempts_today": blocked,
        "geofence_violations_today": geofence_violations,
    }


# ===== Have I Been Pwned Check (admin) =====

@router.post("/check-breach/{user_id}", response_model=BreachCheckResponse)
async def check_user_breach(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Verifica si el email de un usuario aparece en HIBP (solo admin)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    config = await db.scalar(select(SecurityConfig))
    if not config or not config.hibp_api_key:
        raise HTTPException(status_code=400, detail="HIBP API key no configurada")

    breach_data = await check_email_breaches(user.email, config.hibp_api_key)
    if not breach_data:
        raise HTTPException(status_code=503, detail="Servicio HIBP no disponible")

    # Guardar log
    log = BreachCheckLog(
        user_id=user.id,
        email=user.email,
        breaches_found=breach_data.get("count", 0),
        breach_names=", ".join(breach_data.get("names", [])),
    )
    db.add(log)
    await db.commit()

    return {
        "email": user.email,
        "found": breach_data.get("found", False),
        "count": breach_data.get("count", 0),
        "names": breach_data.get("names", []),
        "checked_at": datetime.now(timezone.utc),
    }


# ===== Security Metrics Dashboard =====

@router.get("/metrics")
async def get_security_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Dashboard metrics: logins, countries, devices, timeline (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Total logins last 24h
    total_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == True,
            UserLoginLog.created_at >= since,
        )
    )

    # Failed logins last 24h
    failed_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == False,
            UserLoginLog.created_at >= since,
        )
    )

    # Unique users last 24h
    unique_users = await db.scalar(
        select(func.count(func.distinct(UserLoginLog.user_id))).where(
            UserLoginLog.created_at >= since,
        )
    )

    # Active sessions
    active_sessions = await db.scalar(
        select(func.count(UserSession.id)).where(
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    # Top countries
    country_result = await db.execute(
        select(UserLoginLog.country, func.count(UserLoginLog.id).label("count"))
        .where(UserLoginLog.created_at >= since, UserLoginLog.country.isnot(None))
        .group_by(UserLoginLog.country)
        .order_by(func.count(UserLoginLog.id).desc())
        .limit(5)
    )
    top_countries = [{"country": c or "?", "count": n} for c, n in country_result.all()]

    # Login timeline (hourly)
    hour_trunc = func.date_trunc("hour", UserLoginLog.created_at).label("hour")
    timeline_result = await db.execute(
        select(
            hour_trunc,
            func.count(UserLoginLog.id).label("total"),
            func.sum(case((UserLoginLog.success == False, 1), else_=0)).label("failed"),
        )
        .where(UserLoginLog.created_at >= since)
        .group_by(hour_trunc)
        .order_by(hour_trunc)
    )
    login_timeline = [
        {"hour": h.isoformat() if h else None, "logins": int(t or 0), "failed": int(f or 0)}
        for h, t, f in timeline_result.all()
    ]

    # Device breakdown (simplified: mobile vs desktop from UA)
    device_result = await db.execute(
        select(UserLoginLog.user_agent, func.count(UserLoginLog.id).label("count"))
        .where(UserLoginLog.created_at >= since, UserLoginLog.user_agent.isnot(None))
        .group_by(UserLoginLog.user_agent)
    )
    mobile = 0
    desktop = 0
    other = 0
    for ua, count in device_result.all():
        ua_lower = (ua or "").lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            mobile += count
        elif "mozilla" in ua_lower or "chrome" in ua_lower or "safari" in ua_lower:
            desktop += count
        else:
            other += count

    device_breakdown = [
        {"type": "mobile", "count": mobile},
        {"type": "desktop", "count": desktop},
        {"type": "other", "count": other},
    ]

    return {
        "total_logins_24h": total_logins or 0,
        "failed_logins_24h": failed_logins or 0,
        "unique_users_24h": unique_users or 0,
        "active_sessions": active_sessions or 0,
        "avg_risk_score": 0.0,  # Placeholder for future risk scoring
        "top_countries": top_countries,
        "login_timeline": login_timeline,
        "device_breakdown": device_breakdown,
    }


@router.get("/audit-report")
async def get_audit_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Reporte de auditoría de seguridad de los últimos 7 días (solo admin)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(UserLoginLog.created_at >= week_ago)
    )
    failed_logins = await db.scalar(
        select(func.count(UserLoginLog.id)).where(
            UserLoginLog.success == False,
            UserLoginLog.created_at >= week_ago,
        )
    )
    data_access_count = await db.scalar(
        select(func.count(DataAccessLog.id)).where(DataAccessLog.created_at >= week_ago)
    )
    rotations = await db.scalar(
        select(func.count(SecretRotationLog.id)).where(SecretRotationLog.created_at >= week_ago)
    )
    cleanups = await db.scalar(
        select(func.count(DataRetentionLog.id)).where(DataRetentionLog.started_at >= week_ago)
    )
    records_deleted = await db.scalar(
        select(func.coalesce(func.sum(DataRetentionLog.records_deleted), 0)).where(
            DataRetentionLog.started_at >= week_ago
        )
    )
    active_sessions = await db.scalar(
        select(func.count(UserSession.id)).where(
            UserSession.is_revoked == False,
            UserSession.expires_at > now,
        )
    )

    return {
        "period": f"{week_ago.date()} to {now.date()}",
        "total_logins_7d": total_logins or 0,
        "failed_logins_7d": failed_logins or 0,
        "failed_rate_pct": round((failed_logins / total_logins * 100), 2) if total_logins else 0.0,
        "data_access_logs_7d": data_access_count or 0,
        "secret_rotations_7d": rotations or 0,
        "data_retention_cleanups_7d": cleanups or 0,
        "records_deleted_7d": int(records_deleted or 0),
        "active_sessions_now": active_sessions or 0,
    }
