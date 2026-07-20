"""
Servicio genérico de email transaccional para SellIA.

Reutiliza aiosmtplib pero sin el prefijo [ALERTA SEGURIDAD] y con
plantillas de estilo consistente para todas las comunicaciones.
"""

import os
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.logger import get_logger

logger = get_logger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SellIA")


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> bool:
    """Envía un email transaccional genérico.

    Args:
        to_email: Destinatario
        subject: Asunto
        body_html: Cuerpo HTML
        body_text: Cuerpo texto plano (opcional, se genera desde HTML si no se provee)
        from_email: Email remitente (default: SMTP_FROM)
        from_name: Nombre remitente (default: SellIA)
    """
    if not _smtp_configured():
        logger.warning("SMTP no configurado, email no enviado: %s", subject)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name or SMTP_FROM_NAME} <{from_email or SMTP_FROM}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        text_body = body_text or _html_to_text(body_html)
        part1 = MIMEText(text_body, "plain", "utf-8")
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
        logger.info("Email enviado a %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.error("Error enviando email a %s: %s", to_email, e)
        return False


def _html_to_text(html: str) -> str:
    """Conversión naive HTML → texto plano."""
    import re
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    return text.strip()


def base_email_template(content_html: str, preheader: str = "") -> str:
    """Wrapper de plantilla base con estilo SellIA."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SellIA</title>
<style>
  body {{ margin: 0; padding: 0; background-color: #0a0e1a; font-family: 'Segoe UI', Arial, sans-serif; }}
  .container {{ max-width: 560px; margin: 0 auto; background-color: #0f1525; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.06); }}
  .header {{ background: linear-gradient(135deg, #f97316 0%, #8b5cf6 100%); padding: 28px 24px; text-align: center; }}
  .header h1 {{ margin: 0; color: #fff; font-size: 22px; font-weight: 700; }}
  .body {{ padding: 28px 24px; color: #e2e8f0; font-size: 15px; line-height: 1.6; }}
  .body p {{ margin: 0 0 14px 0; }}
  .body strong {{ color: #f97316; }}
  .body code {{ background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }}
  .cta {{ display: inline-block; margin: 16px 0; padding: 12px 28px; background: linear-gradient(135deg, #f97316 0%, #8b5cf6 100%); color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; }}
  .footer {{ padding: 20px 24px; text-align: center; color: #64748b; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.04); }}
  .footer a {{ color: #f97316; text-decoration: none; }}
  .box {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 16px; margin: 14px 0; }}
  .box-row {{ display: flex; justify-content: space-between; margin: 6px 0; font-size: 14px; }}
  .box-row span:first-child {{ color: #94a3b8; }}
  .box-row span:last-child {{ color: #e2e8f0; font-weight: 500; }}
</style>
</head>
<body>
  <div style="padding: 32px 16px;">
    <div class="container">
      <div class="header">
        <h1>🚀 SellIA</h1>
      </div>
      <div class="body">
        {content_html}
      </div>
      <div class="footer">
        <p>SellIA — Tu Vendedor Automático con IA</p>
        <p><a href="mailto:ventas@sellia.com">ventas@sellia.com</a></p>
        <p style="margin-top:8px;color:#475569;font-size:11px;">Si no esperabas este email, podés ignorarlo.</p>
      </div>
    </div>
  </div>
</body>
</html>"""
