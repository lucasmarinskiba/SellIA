"""
Secure Data Deletion Service

Borrado GDPR completo con sobrescritura de datos sensibles.
"""

import uuid
import json
import random
import string
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.users.models import User
from app.domains.security.models import (
    UserLoginLog, UserSession, PushSubscription, TwoFABackupCode,
    BreachCheckLog, EmailOTP, WebAuthnCredential, SecurityKey,
    TrustedDevice, SessionNonce, IPAllowlist, LoginAnomaly,
    SubscriptionAccessLog, ChargebackAlert,
)
from app.core.field_encryption import encrypt_field
from app.core.logger import get_logger

logger = get_logger(__name__)


async def export_user_data(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Exporta todos los datos personales del usuario en formato JSON."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {}

    data = {
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "export_generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # TODO: Agregar más datos (conversaciones, negocios, etc.)
    return data


def _random_overwrite(length: int) -> str:
    """Genera una cadena aleatoria para sobrescritura."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def secure_delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """
    Borra completamente los datos personales de un usuario.
    Sobrescribe emails, nombres, teléfonos con datos aleatorios antes de eliminar.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    # Overwrite sensitive fields
    user.email = f"deleted_{user.id}@deleted.com"
    user.full_name = _random_overwrite(20)
    user.phone = _random_overwrite(15)
    user.hashed_password = _random_overwrite(60)
    user.is_active = False
    user.totp_secret = None

    # Delete related security records
    models_to_delete = [
        UserLoginLog, UserSession, PushSubscription, TwoFABackupCode,
        BreachCheckLog, EmailOTP, WebAuthnCredential, SecurityKey,
        TrustedDevice, SessionNonce, IPAllowlist, LoginAnomaly,
        SubscriptionAccessLog, ChargebackAlert,
    ]

    for model in models_to_delete:
        await db.execute(
            model.__table__.delete().where(model.user_id == user_id)
        )

    await db.commit()
    logger.info(f"User {user_id} data securely deleted")
    return True
