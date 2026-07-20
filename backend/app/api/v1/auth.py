from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import get_settings

# Optional imports with fallback
try:
    from app.core.turnstile import verify_turnstile_token
except ImportError:
    verify_turnstile_token = None
try:
    from app.core.threat_intel import device_fingerprint
except ImportError:
    device_fingerprint = None
try:
    from app.core.security_notifications import notify_security_event, email_new_device_alert
except ImportError:
    notify_security_event = None
    email_new_device_alert = None
try:
    from app.core.push_notifications import send_security_push
except ImportError:
    send_security_push = None
try:
    from app.core.geo_service import get_ip_geolocation, is_geofence_violation
except ImportError:
    get_ip_geolocation = None
    is_geofence_violation = None
try:
    from app.core.hibp_service import check_email_breaches, format_breach_alert
except ImportError:
    check_email_breaches = None
    format_breach_alert = None
try:
    from app.core.elk_logger import log_login, log_new_device, log_geofence_violation
except ImportError:
    log_login = None
    log_new_device = None
    log_geofence_violation = None

try:
    from app.core.metrics import (
        SELLIA_LOGINS, SELLIA_FAILED_LOGINS, SELLIA_GEOFENCE_VIOLATIONS,
        SELLIA_NEW_DEVICES, SELLIA_ACTIVE_SESSIONS
    )
except ImportError:
    SELLIA_LOGINS = None
    SELLIA_FAILED_LOGINS = None
    SELLIA_GEOFENCE_VIOLATIONS = None
    SELLIA_NEW_DEVICES = None
    SELLIA_ACTIVE_SESSIONS = None

from app.domains.users.models import User
from app.domains.users.schemas import UserCreate, UserResponse, Token

try:
    from app.domains.security.models import (
        UserLoginLog, SecurityConfig, UserSession, TwoFABackupCode, BreachCheckLog
    )
except ImportError:
    UserLoginLog = None
    SecurityConfig = None
    UserSession = None
    TwoFABackupCode = None
    BreachCheckLog = None

try:
    import pyotp
except ImportError:
    pyotp = None
try:
    import qrcode
except ImportError:
    qrcode = None
import io
import base64
import hashlib
import secrets

router = APIRouter()
settings = get_settings()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def _hash_code(code: str) -> str:
    """Hash backup codes with bcrypt (slow, resistant to brute-force)."""
    return get_password_hash(code)


async def _get_or_create_security_config(db: AsyncSession) -> SecurityConfig:
    if SecurityConfig is None:
        return None
    result = await db.execute(select(SecurityConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SecurityConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


async def _check_hibp(db: AsyncSession, user: User, config: SecurityConfig):
    """Verifica Have I Been Pwned y notifica si hay breaches."""
    if not check_email_breaches or not config or not config.alert_on_breach:
        return
    if not config.hibp_api_key:
        return

    breach_data = await check_email_breaches(user.email, config.hibp_api_key)
    if not breach_data or not breach_data.get("found"):
        return

    # Guardar log
    log = BreachCheckLog(
        user_id=user.id,
        email=user.email,
        breaches_found=breach_data["count"],
        breach_names=", ".join(breach_data["names"]),
    )
    db.add(log)
    await db.commit()

    # Notificar
    if notify_security_event:
        await notify_security_event(
            db=db,
            event="breach",
            title="⚠️ Email comprometido detectado",
            description=format_breach_alert(breach_data),
            details={
                "email": user.email,
                "breaches": breach_data["count"],
                "names": breach_data["names"],
            },
            user_email=user.email,
            email_subject="Tu email aparece en filtraciones de datos",
            email_body_text=f"""
Hola {user.full_name},

Tu dirección de email ({user.email}) aparece en {breach_data['count']} filtración(es) de datos conocidas:
{', '.join(breach_data['names'])}

Te recomendamos:
1. Cambiar tu contraseña inmediatamente
2. Activar 2FA si no lo has hecho
3. No reutilizar esta contraseña en otros sitios

Equipo de Seguridad SellIA
""",
            email_body_html=f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;border:1px solid #e0e0e0;border-radius:8px;">
  <h2 style="color:#d32f2f;">⚠️ Tu email aparece en filtraciones</h2>
  <p>Hola <b>{user.full_name}</b>,</p>
  <p>Tu email ({user.email}) aparece en <b>{breach_data['count']}</b> filtración(es) conocidas:</p>
  <ul>{''.join([f'<li>{name}</li>' for name in breach_data['names']])}</ul>
  <a href="/settings/security" style="display:inline-block;padding:12px 24px;background:#d32f2f;color:#fff;text-decoration:none;border-radius:4px;">Cambiar contraseña</a>
</div>
""",
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=3, seconds=3600))],
)
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import get_password_hash

    # Validar Turnstile si está configurado
    if verify_turnstile_token and settings.TURNSTILE_SECRET_KEY:
        turnstile_token = request.headers.get("X-Turnstile-Token")
        valid, msg = await verify_turnstile_token(turnstile_token, request.state.client_ip)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Verificación de seguridad fallida: {msg}")

    result = await db.execute(select(User).where(User.email == user_in.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Enviar email de verificación
    verify_token = create_access_token(
        data={"sub": str(user.id), "scope": "email_verify"},
        expires_delta=timedelta(hours=24),
    )
    verify_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/verify-email?token={verify_token}"
    await _send_verification_email(user.email, user.full_name, verify_url)

    # HIBP check en registro
    config = await _get_or_create_security_config(db)
    if config and config.alert_on_breach:
        await _check_hibp(db, user, config)

    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Timing-attack mitigation: usar hash dummy estático precomputado
    # para que el tiempo de verificación sea similar al de un usuario real
    if user is None:
        _DUMMY_HASH = "$2b$12$dummy.hash.for.timing.attack.mitigation.123456789012"
        verify_password(form_data.password, _DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar email verificado
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED",
        )

    # Verificar bloqueo de cuenta
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intentá más tarde.",
        )

    # Verificar contraseña
    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.now(timezone.utc)

        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            # Revocar todas las sesiones activas al bloquear cuenta
            if UserSession is not None:
                await db.execute(
                    select(UserSession).where(
                        UserSession.user_id == user.id,
                        UserSession.is_revoked == False,
                    )
                )
                # Mark all active sessions as revoked
                from sqlalchemy import update
                await db.execute(
                    update(UserSession)
                    .where(UserSession.user_id == user.id, UserSession.is_revoked == False)
                    .values(is_revoked=True)
                )

        await db.commit()

        # Notificar intento fallido
        if notify_security_event:
            await notify_security_event(
                db=db,
                event="failed_login",
                title="Intento de login fallido",
                description=f"Intento fallido para {user.email}",
                details={"email": user.email, "ip": request.state.client_ip},
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Login exitoso: resetear contadores
    if user.failed_login_attempts > 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_failed_login = None

    # Verificar 2FA
    if user.is_2fa_enabled and user.totp_secret:
        tfa_code = request.headers.get("X-2FA-Code")
        
        # Primero intentar TOTP
        totp_valid = False
        if tfa_code and pyotp:
            totp = pyotp.TOTP(user.totp_secret)
            totp_valid = totp.verify(tfa_code, valid_window=1)
        
        # Si TOTP falla, intentar backup code
        backup_valid = False
        if not totp_valid and tfa_code and TwoFABackupCode is not None:
            code_hash = _hash_code(tfa_code.strip())
            backup_result = await db.execute(
                select(TwoFABackupCode).where(
                    TwoFABackupCode.user_id == user.id,
                    TwoFABackupCode.code_hash == code_hash,
                    TwoFABackupCode.is_used == False,
                )
            )
            backup_code = backup_result.scalar_one_or_none()
            if backup_code:
                backup_valid = True
                backup_code.is_used = True
                backup_code.used_at = datetime.now(timezone.utc)

        if not totp_valid and not backup_valid:
            await db.commit()
            if not tfa_code:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="2FA_REQUIRED",
                    headers={"X-2FA-Required": "true"},
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código 2FA inválido o código de backup ya usado",
            )

    # Geolocalización y geofencing
    geo_data = None
    if get_ip_geolocation:
        geo_data = await get_ip_geolocation(request.state.client_ip)

    country = geo_data.get("country_code") if geo_data else None
    city = geo_data.get("city") if geo_data else None
    current_lat = geo_data.get("latitude") if geo_data else None
    current_lon = geo_data.get("longitude") if geo_data else None

    # Geofencing check
    config = await _get_or_create_security_config(db)
    geofence_violation = False
    distance_km = 0.0
    
    if config and config.max_distance_km and is_geofence_violation:
        # Buscar último login exitoso con coordenadas
        last_login_result = await db.execute(
            select(UserLoginLog)
            .where(
                UserLoginLog.user_id == user.id,
                UserLoginLog.success == True,
                UserLoginLog.latitude.isnot(None),
            )
            .order_by(UserLoginLog.created_at.desc())
            .limit(1)
        )
        last_login = last_login_result.scalar_one_or_none()
        
        if last_login and last_login.latitude and last_login.longitude:
            geofence_violation, distance_km = is_geofence_violation(
                last_login.latitude,
                last_login.longitude,
                current_lat,
                current_lon,
                config.max_distance_km,
            )

    # Device fingerprint y detección de nuevo dispositivo
    current_fingerprint = ""
    if device_fingerprint:
        current_fingerprint = device_fingerprint(
            request.state.client_ip,
            request.headers.get("user-agent"),
            request.headers.get("accept-language"),
        )

    is_new_device = user.last_device_fingerprint and user.last_device_fingerprint != current_fingerprint
    if is_new_device and SELLIA_NEW_DEVICES:
        SELLIA_NEW_DEVICES.inc()

    # Actualizar último login
    user.last_login_at = datetime.now(timezone.utc)
    user.last_device_fingerprint = current_fingerprint
    await db.commit()

    # Métricas de login exitoso
    if SELLIA_LOGINS:
        SELLIA_LOGINS.labels(status="success").inc()

    # Registrar login con geolocalización
    if UserLoginLog is not None:
        login_log = UserLoginLog(
            user_id=user.id,
            ip_address=request.state.client_ip,
            user_agent=request.headers.get("user-agent"),
            device_fingerprint=current_fingerprint,
            country=country,
            city=city,
            latitude=current_lat,
            longitude=current_lon,
            success=True,
        )
        db.add(login_log)
        await db.commit()

    # Log to ELK
    if log_login:
        try:
            await log_login(
                email=user.email,
                ip=request.state.client_ip,
                country=country,
                success=True,
                user_id=str(user.id),
                extra={"device_fingerprint": current_fingerprint, "city": city},
            )
        except Exception:
            pass

    # Alerta de geofencing
    if geofence_violation and SELLIA_GEOFENCE_VIOLATIONS:
        SELLIA_GEOFENCE_VIOLATIONS.inc()

    if geofence_violation and notify_security_event:
        await notify_security_event(
            db=db,
            event="geofence",
            title="🌍 Login desde ubicación inesperada",
            description=f"Login desde {distance_km:.0f} km de tu última ubicación",
            details={
                "email": user.email,
                "ip": request.state.client_ip,
                "distance_km": round(distance_km, 2),
                "country": country,
                "city": city,
            },
            user_email=user.email,
            email_subject="Login desde ubicación inesperada",
            email_body_text=f"""
Hola {user.full_name},

Detectamos un inicio de sesión desde una ubicación inesperada.

Distancia desde tu último login: {distance_km:.0f} km
Ubicación actual: {city or 'Desconocido'}, {country or 'Desconocido'}
IP: {request.state.client_ip}

Si no fuiste vos, cambiá tu contraseña inmediatamente.
""",
            email_body_html=f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;border:1px solid #e0e0e0;border-radius:8px;">
  <h2 style="color:#d32f2f;">🌍 Login desde ubicación inesperada</h2>
  <p>Hola <b>{user.full_name}</b>,</p>
  <p>Detectamos un login a <b>{distance_km:.0f} km</b> de tu última ubicación.</p>
  <table style="width:100%;background:#f5f5f5;padding:12px;border-radius:6px;margin:16px 0;">
    <tr><td><b>Ubicación:</b></td><td>{city or 'Desconocido'}, {country or 'Desconocido'}</td></tr>
    <tr><td><b>IP:</b></td><td>{request.state.client_ip}</td></tr>
  </table>
  <a href="/settings/security" style="display:inline-block;padding:12px 24px;background:#d32f2f;color:#fff;text-decoration:none;border-radius:4px;">Cambiar contraseña</a>
</div>
""",
        )

    # Log geofence violation to ELK
    if geofence_violation and log_geofence_violation:
        try:
            await log_geofence_violation(
                email=user.email,
                ip=request.state.client_ip,
                distance_km=distance_km,
                country=country,
                user_id=str(user.id),
            )
        except Exception:
            pass

    # Notificar nuevo dispositivo
    if is_new_device and notify_security_event:
        html, text = email_new_device_alert(
            user_name=user.full_name,
            ip=request.state.client_ip,
            country=country,
            user_agent=request.headers.get("user-agent", ""),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await notify_security_event(
            db=db,
            event="new_device",
            title="Nuevo dispositivo detectado",
            description=f"Login desde nuevo dispositivo para {user.email}",
            details={
                "email": user.email,
                "ip": request.state.client_ip,
                "country": country,
                "city": city,
                "fingerprint": current_fingerprint,
            },
            user_email=user.email,
            email_subject="Nuevo inicio de sesión detectado",
            email_body_html=html,
            email_body_text=text,
        )

    # Log new device to ELK
    if is_new_device and log_new_device:
        try:
            await log_new_device(
                email=user.email,
                ip=request.state.client_ip,
                country=country,
                user_id=str(user.id),
                device_info=request.headers.get("user-agent"),
            )
        except Exception:
            pass

    # Push notification
    if is_new_device and send_security_push:
        try:
            await send_security_push(
                db=db,
                user_id=str(user.id),
                event="new_device",
                title="🔐 Nuevo dispositivo detectado",
                body=f"Alguien inició sesión desde {request.state.client_ip} ({country or 'Desconocido'}). Si no fuiste vos, cambiá tu contraseña.",
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Push notification error: {e}")

    # HIBP check en login
    if config and config.alert_on_breach:
        await _check_hibp(db, user, config)

    # Actualizar métricas de sesiones activas
    if SELLIA_ACTIVE_SESSIONS and UserSession is not None:
        try:
            result = await db.execute(
                select(func.count()).select_from(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.is_revoked == False,
                    UserSession.expires_at > datetime.now(timezone.utc)
                )
            )
            SELLIA_ACTIVE_SESSIONS.set(result.scalar() or 0)
        except Exception:
            pass

    # Crear token y sesión
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    if UserSession is not None:
        session_hash = hashlib.sha256(access_token.encode()).hexdigest()[:64]
        user_session = UserSession(
            user_id=user.id,
            session_token=session_hash,
            device_name=request.headers.get("user-agent", "")[:50],
            device_fingerprint=current_fingerprint,
            ip_address=request.state.client_ip,
            user_agent=request.headers.get("user-agent"),
            country=country,
            expires_at=datetime.now(timezone.utc) + access_token_expires,
        )
        db.add(user_session)
        await db.commit()

    # Cookie httpOnly segura
    cookie_secure = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")

    if token and UserSession is not None:
        session_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_token == session_hash,
                UserSession.is_revoked == False,
            )
        )
        session_record = result.scalar_one_or_none()
        if session_record:
            session_record.is_revoked = True
            await db.commit()

    response.delete_cookie(key="access_token", path="/")
    return {"detail": "Sesión cerrada correctamente"}


# ===== 2FA Endpoints =====

@router.post("/2fa/setup")
async def setup_2fa(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    from app.core.deps import get_current_user
    user = await get_current_user(request, db)

    if user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA ya está activado")

    if not pyotp:
        raise HTTPException(status_code=500, detail="Módulo 2FA no disponible")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="SellIA",
    )

    # Generar QR code
    qr = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode()

    # Guardar secreto temporalmente
    user.totp_secret = secret
    await db.commit()

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "provisioning_uri": provisioning_uri,
        "message": "Escaneá el QR con Google Authenticator, Authy o similar",
    }


@router.post("/2fa/verify")
async def verify_2fa_setup(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    from app.core.deps import get_current_user
    user = await get_current_user(request, db)

    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="No hay configuración de 2FA pendiente")

    if not pyotp:
        raise HTTPException(status_code=500, detail="Módulo 2FA no disponible")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto")

    user.is_2fa_enabled = True
    await db.commit()

    # Generar códigos de backup
    if TwoFABackupCode is not None:
        backup_codes = []
        for _ in range(8):
            code_plain = secrets.token_hex(4).upper()  # 8 chars hex
            code_hash = _hash_code(code_plain)
            bc = TwoFABackupCode(user_id=user.id, code_hash=code_hash)
            db.add(bc)
            backup_codes.append(code_plain)
        await db.commit()

        return {
            "message": "2FA activado correctamente",
            "backup_codes": backup_codes,
            "warning": "Guardá estos códigos en un lugar seguro. Solo se muestran una vez.",
        }

    return {"message": "2FA activado correctamente"}


@router.post("/2fa/disable")
async def disable_2fa(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    from app.core.deps import get_current_user
    user = await get_current_user(request, db)

    if not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA no está activado")

    if not pyotp:
        raise HTTPException(status_code=500, detail="Módulo 2FA no disponible")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto")

    user.is_2fa_enabled = False
    user.totp_secret = None
    await db.commit()

    # Eliminar códigos de backup
    if TwoFABackupCode is not None:
        await db.execute(
            select(TwoFABackupCode).where(TwoFABackupCode.user_id == user.id)
        )
        # SQLAlchemy delete
        from sqlalchemy import delete
        await db.execute(delete(TwoFABackupCode).where(TwoFABackupCode.user_id == user.id))
        await db.commit()

    return {"message": "2FA desactivado correctamente"}


@router.get("/2fa/backup-codes")
async def list_backup_codes_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve cuántos códigos de backup quedan disponibles."""
    from app.core.deps import get_current_user
    user = await get_current_user(request, db)

    if not user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA no está activado")

    if TwoFABackupCode is None:
        return {"remaining": 0}

    result = await db.execute(
        select(TwoFABackupCode).where(
            TwoFABackupCode.user_id == user.id,
            TwoFABackupCode.is_used == False,
        )
    )
    remaining = len(result.scalars().all())
    return {"remaining": remaining}


# ============================================================
#  Email OTP
# ============================================================

async def _send_verification_email(to_email: str, full_name: str, verify_url: str):
    """Envía email de verificación de cuenta."""
    try:
        from app.core.email_service import send_email
        subject = "Verificá tu cuenta de SellIA"
        html = f'''<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;border:1px solid #e0e0e0;border-radius:8px;">
  <h2 style="color:#4f46e5;">¡Bienvenido a SellIA, {full_name}!</h2>
  <p>Para activar tu cuenta, hacé clic en el siguiente botón:</p>
  <a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;text-decoration:none;border-radius:4px;">Verificar mi cuenta</a>
  <p style="margin-top:16px;color:#666;font-size:12px;">El link expira en 24 horas. Si no creaste esta cuenta, ignorá este email.</p>
</div>'''
        text = f'''Hola {full_name},

Para activar tu cuenta de SellIA, visitá este link (válido por 24 horas):
{verify_url}

Si no creaste esta cuenta, ignorá este email.
'''
        await send_email(to_email, subject, html, text)
    except Exception:
        pass


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verifica el email del usuario con un token JWT de un solo uso."""
    payload = decode_access_token(token)
    if not payload or payload.get("scope") != "email_verify":
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token inválido")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.email_verified:
        return {"message": "Email ya verificado"}

    user.email_verified = True
    await db.commit()
    return {"message": "Email verificado correctamente. Ya podés iniciar sesión."}


@router.post("/resend-verification", dependencies=[Depends(RateLimiter(times=3, seconds=300))])
async def resend_verification(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reenvía el email de verificación. Requiere autenticación."""
    from app.core.deps import get_current_user
    user = await get_current_user(request, db)
    if user.email_verified:
        return {"message": "Email ya verificado"}

    verify_token = create_access_token(
        data={"sub": str(user.id), "scope": "email_verify"},
        expires_delta=timedelta(hours=24),
    )
    verify_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/verify-email?token={verify_token}"
    await _send_verification_email(user.email, user.full_name, verify_url)
    return {"message": "Email de verificación reenviado"}


@router.post("/2fa/email/send", dependencies=[Depends(RateLimiter(times=3, seconds=300))])
async def send_email_otp(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Envía un código OTP por email."""
    from app.core.deps import get_current_user
    from app.core.email_otp import create_email_otp, send_otp_email

    user = await get_current_user(request, db)
    code = await create_email_otp(db, user.id, "login", ip_address=request.state.client_ip)
    await send_otp_email(user.email, code, "login")
    return {"message": "Código enviado a tu email"}


@router.post("/2fa/email/verify")
async def verify_email_otp_endpoint(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verifica un código OTP por email."""
    from app.core.deps import get_current_user
    from app.core.email_otp import verify_email_otp

    user = await get_current_user(request, db)
    valid = await verify_email_otp(db, user.id, code, "login")
    if not valid:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    return {"message": "Código verificado correctamente"}


# ============================================================
#  WebAuthn / Passkeys
# ============================================================

@router.post("/webauthn/register-begin")
async def webauthn_register_begin(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Inicia registro de passkey."""
    from app.core.deps import get_current_user
    from app.core.webauthn_service import generate_registration_options

    user = await get_current_user(request, db)
    options = generate_registration_options(user.id, user.email)
    return options


@router.post("/webauthn/register-finish")
async def webauthn_register_finish(
    credential_id: str,
    public_key: str,
    device_name: str = "Passkey",
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Finaliza registro de passkey."""
    from app.core.deps import get_current_user
    from app.core.webauthn_service import register_credential

    user = await get_current_user(request, db)
    await register_credential(db, user.id, credential_id, public_key, device_name=device_name)
    return {"message": "Passkey registrado correctamente"}


@router.post("/webauthn/login-begin")
async def webauthn_login_begin():
    """Inicia login con passkey."""
    from app.core.webauthn_service import generate_authentication_options
    return generate_authentication_options()


@router.get("/webauthn/credentials")
async def list_webauthn_credentials(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Lista passkeys registrados."""
    from app.core.deps import get_current_user
    from app.core.webauthn_service import get_user_credentials

    user = await get_current_user(request, db)
    creds = await get_user_credentials(db, user.id)
    return [
        {"id": str(c.id), "device_name": c.device_name, "last_used": c.last_used_at, "created_at": c.created_at}
        for c in creds
    ]


@router.delete("/webauthn/credentials/{cred_id}")
async def delete_webauthn_credential(
    cred_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Elimina un passkey."""
    from app.core.deps import get_current_user
    from app.core.webauthn_service import remove_credential

    user = await get_current_user(request, db)
    success = await remove_credential(db, cred_id)
    if not success:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    return {"message": "Passkey eliminado"}


# ============================================================
#  Trusted Devices
# ============================================================

@router.get("/devices")
async def list_trusted_devices(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Lista dispositivos del usuario."""
    from app.core.deps import get_current_user
    from app.core.trusted_devices import list_user_devices

    user = await get_current_user(request, db)
    devices = await list_user_devices(db, user.id)
    return [
        {
            "id": str(d.id),
            "device_name": d.device_name,
            "os": d.os,
            "browser": d.browser,
            "ip": d.ip_address,
            "country": d.country,
            "first_seen": d.first_seen_at,
            "last_seen": d.last_seen_at,
            "is_trusted": d.is_trusted,
            "is_blocked": d.is_blocked,
        }
        for d in devices
    ]


@router.post("/devices/{device_id}/trust")
async def trust_device_endpoint(
    device_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Marca un dispositivo como de confianza."""
    from app.core.deps import get_current_user
    from app.core.trusted_devices import trust_device

    user = await get_current_user(request, db)
    device = await trust_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return {"message": "Dispositivo confiado"}


@router.post("/devices/{device_id}/block")
async def block_device_endpoint(
    device_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Bloquea un dispositivo."""
    from app.core.deps import get_current_user
    from app.core.trusted_devices import block_device

    user = await get_current_user(request, db)
    device = await block_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return {"message": "Dispositivo bloqueado"}


# ============================================================
#  Data Export / Deletion
# ============================================================

@router.get("/me/export-data")
async def export_my_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Exporta todos los datos personales del usuario."""
    from app.core.deps import get_current_user
    from app.core.data_deletion import export_user_data

    user = await get_current_user(request, db)
    data = await export_user_data(db, user.id)
    return data


@router.post("/me/delete-account")
async def delete_my_account(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Borra la cuenta del usuario (GDPR)."""
    from app.core.deps import get_current_user
    from app.core.data_deletion import secure_delete_user

    user = await get_current_user(request, db)
    success = await secure_delete_user(db, user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Error al eliminar la cuenta")
    return {"message": "Cuenta eliminada correctamente"}
