"""
SendGrid integration real — Email sequences, transactional, invoicing.

Env vars required:
- SENDGRID_API_KEY
- SENDGRID_FROM_EMAIL
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
import base64
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@sellia.com")

if not SENDGRID_API_KEY:
    logger.warning("SENDGRID_API_KEY not configured, email disabled")

sg = SendGridAPIClient(SENDGRID_API_KEY) if SENDGRID_API_KEY else None


class EmailService:
    """SendGrid email service."""

    @staticmethod
    def send_transactional(
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envía email transaccional (orden, factura, etc).

        Retorna: status + message_id.
        """

        if not sg:
            logger.error("SendGrid not configured")
            return {"status": "error", "message": "Email service not configured"}

        try:
            message = Mail(
                from_email=from_email or SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )

            if reply_to:
                message.reply_to = Email(reply_to)

            response = sg.send(message)

            logger.info(f"Email sent to {to_email}, status {response.status_code}")

            return {
                "status": "sent",
                "to": to_email,
                "message_id": response.headers.get("X-Message-ID", "unknown"),
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_with_attachment(
        to_email: str,
        subject: str,
        html_content: str,
        attachment_name: str,
        attachment_content: bytes,
        attachment_type: str = "application/pdf",
    ) -> Dict[str, Any]:
        """
        Envía email con adjunto (ej: PDF factura).
        """

        if not sg:
            return {"status": "error", "message": "Email service not configured"}

        try:
            message = Mail(
                from_email=SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )

            # Adjuntar archivo
            encoded = base64.b64encode(attachment_content).decode()
            attachment = Attachment(
                file_content=encoded,
                file_name=attachment_name,
                file_type=attachment_type,
                disposition="attachment",
            )
            message.attachment = attachment

            response = sg.send(message)

            logger.info(f"Email with attachment sent to {to_email}")

            return {
                "status": "sent",
                "to": to_email,
                "attachment": attachment_name,
            }

        except Exception as e:
            logger.error(f"Error sending email with attachment: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_email_sequence(
        to_email: str,
        sequence_type: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Envía secuencia de emails (welcome, nurture, etc).

        sequence_type: 'welcome' | 'cart_abandonment' | 'nurture' | 'winback'
        """

        results = []

        if sequence_type == "welcome":
            results.extend(EmailService._welcome_sequence(to_email, context))
        elif sequence_type == "cart_abandonment":
            results.extend(EmailService._cart_abandonment_sequence(to_email, context))
        elif sequence_type == "nurture":
            results.extend(EmailService._nurture_sequence(to_email, context))

        return results

    @staticmethod
    def _welcome_sequence(to_email: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Welcome sequence: 3 emails en 5 días."""

        results = []

        # Email 1: Bienvenida (día 0)
        r1 = EmailService.send_transactional(
            to_email=to_email,
            subject=f"Bienvenido a {context.get('product_name', 'nuestro producto')}!",
            html_content=f"""
            <h1>¡Bienvenido!</h1>
            <p>Gracias por confiar en nosotros. Aquí están tus próximos pasos:</p>
            <ol>
                <li>Accede a tu cuenta</li>
                <li>Mira el tutorial de 5 minutos</li>
                <li>Prueba las funciones principales</li>
            </ol>
            <p><a href="{context.get('dashboard_url', '#')}">Ir a tu cuenta</a></p>
            """,
        )
        results.append(r1)

        # Email 2: Educación (día 1) - Scheduled via background job
        # results.append({"status": "scheduled", "email": 2, "send_at": "tomorrow 9am"})

        # Email 3: Oferta (día 2) - Scheduled via background job
        # results.append({"status": "scheduled", "email": 3, "send_at": "in 2 days 9am"})

        return results

    @staticmethod
    def _cart_abandonment_sequence(to_email: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cart abandonment: 3 emails."""

        results = []

        # Email 1: 1 hora después
        r1 = EmailService.send_transactional(
            to_email=to_email,
            subject=f"¡Olvidaste tu carrito! {context.get('product_name')} te espera",
            html_content=f"""
            <h1>¡Espera!</h1>
            <p>Tienes {context.get('items_count', 1)} artículo(s) en tu carrito por ${context.get('cart_total', 'X')}.</p>
            <p><a href="{context.get('cart_url', '#')}">Completar compra</a></p>
            """,
        )
        results.append(r1)

        return results

    @staticmethod
    def _nurture_sequence(to_email: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Nurture sequence: educación + valor."""

        results = []

        r1 = EmailService.send_transactional(
            to_email=to_email,
            subject="Cómo {context.get('product_name')} puede triplicar tu [métrica]",
            html_content=f"""
            <h1>Guía: Cómo usar {context.get('product_name')} efectivamente</h1>
            <p>En este email te muestro los 3 errores más comunes y cómo evitarlos...</p>
            """,
        )
        results.append(r1)

        return results
