"""
Sistema de notificaciones de seguridad:
- Emails de alerta (login desde nuevo dispositivo, intentos fallidos, malware)
- Webhooks a Slack, Discord, Telegram
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.security.models import SecurityWebhook, SecurityConfig

settings = get_settings()

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


async def send_security_email(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    """Envía un email de alerta de seguridad."""
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = f"[ALERTA SEGURIDAD] {subject}"

        part1 = MIMEText(body_text, "plain", "utf-8")
        part2 = MIMEText(body_html, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
        return True
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Email error: {e}")
        return False


def format_slack_message(event: str, title: str, description: str, details: dict) -> dict:
    """Formatea un mensaje para Slack."""
    color = "danger" if event in ("malware", "brute_force", "suspicious_login") else "warning"
    return {
        "attachments": [
            {
                "color": color,
                "title": f"🛡️ {title}",
                "text": description,
                "fields": [
                    {"title": k.replace("_", " ").title(), "value": str(v)[:100], "short": True}
                    for k, v in details.items()
                ],
                "footer": "SellIA Security",
                "ts": int(datetime.now(timezone.utc).timestamp()),
            }
        ]
    }


def format_discord_message(event: str, title: str, description: str, details: dict) -> dict:
    """Formatea un mensaje para Discord."""
    color = 0xFF0000 if event in ("malware", "brute_force", "suspicious_login") else 0xFFA500
    fields = [
        {"name": k.replace("_", " ").title(), "value": str(v)[:1000], "inline": True}
        for k, v in details.items()
    ]
    return {
        "embeds": [
            {
                "title": f"🛡️ {title}",
                "description": description,
                "color": color,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "SellIA Security"},
            }
        ]
    }


def format_telegram_message(title: str, description: str, details: dict) -> str:
    """Formatea un mensaje para Telegram (texto plano)."""
    lines = [f"🛡️ *{title}*", f"{description}", ""]
    for k, v in details.items():
        lines.append(f"• {k.replace('_', ' ').title()}: `{str(v)[:200]}`")
    return "\n".join(lines)


async def send_webhook(webhook: SecurityWebhook, event: str, title: str, description: str, details: dict):
    """Envía una alerta a un webhook configurado."""
    if not webhook.is_active:
        return

    # Filtrar por eventos suscritos
    if webhook.events and event not in webhook.events.split(","):
        return

    try:
        if webhook.platform == "slack":
            payload = format_slack_message(event, title, description, details)
        elif webhook.platform == "discord":
            payload = format_discord_message(event, title, description, details)
        elif webhook.platform == "telegram":
            # Telegram usa el URL como https://api.telegram.org/bot<TOKEN>/sendMessage
            # o un webhook genérico que redirige
            text = format_telegram_message(title, description, details)
            payload = {"text": text, "parse_mode": "Markdown"}
        else:
            payload = {
                "event": event,
                "title": title,
                "description": description,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            import hashlib
            import hmac
            import json as _json
            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                payload_bytes = _json.dumps(payload, default=str, separators=(",", ":")).encode()
                signature = hmac.new(
                    webhook.secret.encode(),
                    payload_bytes,
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Security-Signature"] = signature

            response = await client.post(webhook.url, json=payload, headers=headers)
            response.raise_for_status()

    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Webhook error ({webhook.name}): {e}")


async def notify_security_event(
    db: AsyncSession,
    event: str,
    title: str,
    description: str,
    details: dict,
    user_email: Optional[str] = None,
    email_subject: Optional[str] = None,
    email_body_html: Optional[str] = None,
    email_body_text: Optional[str] = None,
):
    """
    Notifica un evento de seguridad por todos los canales configurados:
    - Emails al usuario (si se proporciona)
    - Webhooks (Slack, Discord, Telegram)
    """
    # 1. Enviar email al usuario
    if user_email and email_subject and email_body_text:
        await send_security_email(user_email, email_subject, email_body_html or email_body_text, email_body_text)

    # 2. Enviar a webhooks activos
    try:
        result = await db.execute(select(SecurityWebhook).where(SecurityWebhook.is_active == True))
        webhooks = result.scalars().all()
        for wh in webhooks:
            await send_webhook(wh, event, title, description, details)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Error fetching webhooks: {e}")


# Plantillas de email predefinidas

def email_new_device_alert(user_name: str, ip: str, country: str, user_agent: str, timestamp: str) -> tuple[str, str]:
    """Retorna (html, text) para alerta de nuevo dispositivo."""
    text = f"""
Hola {user_name},

Detectamos un inicio de sesión desde un dispositivo o ubicación nueva.

Detalles:
- IP: {ip}
- País: {country or 'Desconocido'}
- Dispositivo: {user_agent or 'Desconocido'}
- Fecha: {timestamp}

Si no fuiste vos, cambiá tu contraseña inmediatamente desde:
https://tusitio.com/settings/security

Equipo de Seguridad SellIA
"""
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;border:1px solid #e0e0e0;border-radius:8px;">
  <h2 style="color:#d32f2f;">🔐 Nuevo inicio de sesión detectado</h2>
  <p>Hola <b>{user_name}</b>,</p>
  <p>Detectamos un inicio de sesión desde un dispositivo o ubicación nueva.</p>
  <table style="width:100%;background:#f5f5f5;padding:12px;border-radius:6px;margin:16px 0;">
    <tr><td><b>IP:</b></td><td>{ip}</td></tr>
    <tr><td><b>País:</b></td><td>{country or 'Desconocido'}</td></tr>
    <tr><td><b>Dispositivo:</b></td><td>{user_agent or 'Desconocido'}</td></tr>
    <tr><td><b>Fecha:</b></td><td>{timestamp}</td></tr>
  </table>
  <p style="color:#d32f2f;font-weight:bold;">¿No fuiste vos?</p>
  <a href="https://tusitio.com/settings/security" style="display:inline-block;padding:12px 24px;background:#d32f2f;color:#fff;text-decoration:none;border-radius:4px;">Cambiar contraseña</a>
  <p style="margin-top:20px;font-size:12px;color:#888;">Equipo de Seguridad SellIA</p>
</div>
"""
    return html, text
