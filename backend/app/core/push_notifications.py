"""
Servicio de notificaciones push Web Push.
Usa VAPID para autenticación con los servidores push de navegadores.
"""

import os
import json
import base64
from datetime import datetime, timezone
from typing import Optional

try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    webpush = None
    WebPushException = Exception
    WEBPUSH_AVAILABLE = False

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.security.models import PushSubscription

# VAPID keys (generar con: openssl ecparam -genkey -name prime256v1 -noout -out vapid_private.pem)
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS = {
    "sub": os.getenv("VAPID_SUBJECT", "mailto:security@tusitio.com"),
}

DEFAULT_VAPID_PUBLIC_KEY = os.getenv("NEXT_PUBLIC_VAPID_PUBLIC_KEY", VAPID_PUBLIC_KEY)


def get_vapid_public_key() -> str:
    """Devuelve la clave pública VAPID para que el frontend se suscriba."""
    return DEFAULT_VAPID_PUBLIC_KEY


async def send_push_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    body: str,
    icon: str = "/icon-192x192.png",
    badge: str = "/badge-72x72.png",
    url: str = "/dashboard",
    tag: str = "security-alert",
    require_interaction: bool = True,
):
    """
    Envía una notificación push a todas las suscripciones activas de un usuario.
    """
    if not WEBPUSH_AVAILABLE:
        from app.core.logger import get_logger
        get_logger(__name__).warning("pywebpush no instalado. Push omitido.")
        return

    if not VAPID_PRIVATE_KEY:
        from app.core.logger import get_logger
        get_logger(__name__).warning("VAPID_PRIVATE_KEY no configurada. Push omitido.")
        return

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True,
        )
    )
    subscriptions = result.scalars().all()

    if not subscriptions:
        return

    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": icon,
        "badge": badge,
        "url": url,
        "tag": tag,
        "requireInteraction": require_interaction,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
        except WebPushException as e:
            # Si la suscripción expiró o fue eliminada, desactivarla
            if e.response and e.response.status_code in (410, 404):
                sub.is_active = False
                await db.commit()
            else:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Error enviando push: {e}")
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Error inesperado: {e}")


async def send_security_push(
    db: AsyncSession,
    user_id: str,
    event: str,
    title: str,
    body: str,
):
    """Envía una notificación push de seguridad."""
    await send_push_notification(
        db=db,
        user_id=user_id,
        title=title,
        body=body,
        url="/dashboard/security",
        tag=f"security-{event}",
        require_interaction=True,
    )
