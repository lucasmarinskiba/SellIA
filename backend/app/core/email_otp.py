"""
Email OTP Service

Genera y verifica códigos OTP enviados por email para:
- Login alternativo a TOTP
- Verificación de dispositivo nuevo
- Reset de contraseña seguro
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.security.models import EmailOTP
from app.core.logger import get_logger

logger = get_logger(__name__)

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10


def generate_otp() -> str:
    """Genera un código OTP de 6 dígitos."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    """Hashea el OTP con SHA-256."""
    return hashlib.sha256(code.encode()).hexdigest()


async def create_email_otp(
    db: AsyncSession,
    user_id: uuid.UUID,
    purpose: str,
    ip_address: Optional[str] = None,
) -> str:
    """Crea un OTP y lo guarda en la BD. Retorna el código en claro (solo para enviar)."""
    code = generate_otp()
    code_hash = hash_otp(code)

    # Invalidar OTPs anteriores del mismo propósito
    await invalidate_previous_otps(db, user_id, purpose)

    otp = EmailOTP(
        user_id=user_id,
        code_hash=code_hash,
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        ip_address=ip_address,
    )
    db.add(otp)
    await db.commit()
    await db.refresh(otp)

    logger.info(f"Created email OTP for user {user_id}, purpose {purpose}")
    return code


async def verify_email_otp(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
    purpose: str,
) -> bool:
    """Verifica un OTP y lo marca como usado."""
    code_hash = hash_otp(code)

    result = await db.execute(
        select(EmailOTP).where(
            EmailOTP.user_id == user_id,
            EmailOTP.code_hash == code_hash,
            EmailOTP.purpose == purpose,
            EmailOTP.is_used == False,
            EmailOTP.expires_at > datetime.now(timezone.utc),
        )
    )
    otp = result.scalar_one_or_none()

    if not otp:
        return False

    otp.is_used = True
    otp.used_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Verified email OTP for user {user_id}, purpose {purpose}")
    return True


async def invalidate_previous_otps(db: AsyncSession, user_id: uuid.UUID, purpose: str) -> None:
    """Invalida OTPs anteriores del mismo propósito."""
    result = await db.execute(
        select(EmailOTP).where(
            EmailOTP.user_id == user_id,
            EmailOTP.purpose == purpose,
            EmailOTP.is_used == False,
        )
    )
    for otp in result.scalars().all():
        otp.is_used = True
    await db.commit()


async def send_otp_email(email: str, code: str, purpose: str) -> None:
    """Envía el OTP por email usando el servicio SMTP existente."""
    from app.core.security_notifications import send_email

    subject = "Tu código de verificación"
    if purpose == "login":
        subject = "Código de verificación para iniciar sesión"
    elif purpose == "password_reset":
        subject = "Código para restablecer tu contraseña"
    elif purpose == "device_verify":
        subject = "Verificación de nuevo dispositivo"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
        <h2>{subject}</h2>
        <p>Tu código de verificación es:</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 4px; background: #f0f0f0; padding: 20px; text-align: center; border-radius: 8px;">
            {code}
        </div>
        <p>Este código expira en {OTP_EXPIRY_MINUTES} minutos.</p>
        <p style="color: #999; font-size: 12px;">Si no solicitaste este código, ignorá este email.</p>
    </div>
    """

    try:
        await send_email(to=email, subject=subject, html=html)
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
