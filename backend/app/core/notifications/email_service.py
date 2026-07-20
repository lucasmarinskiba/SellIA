"""
Email Notifications — SES/SendGrid integration.

Soporta:
1. Order confirmation
2. Shipment notification
3. Delivery confirmation
4. Payment failed alert
5. Refund notification
6. Custom templates con personalización
"""

import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import html

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    """Proveedores de email soportados."""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    SMTP = "smtp"


class EmailTemplate(Enum):
    """Templates predefinidas."""
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPMENT_NOTIFICATION = "shipment_notification"
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    PAYMENT_FAILED = "payment_failed"
    REFUND_NOTIFICATION = "refund_notification"
    ACCOUNT_VERIFICATION = "account_verification"
    PROMOTIONAL = "promotional"


@dataclass
class EmailRecipient:
    """Destinatario de email."""
    email: str
    name: Optional[str] = None
    variables: Dict[str, Any] = None


@dataclass
class EmailMessage:
    """Estructura de email."""
    to: List[EmailRecipient]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: str = "noreply@sellia.ai"
    from_name: str = "SellIA"
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, str]]] = None
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class EmailTemplateEngine:
    """Motor de templates con personalización."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[EmailTemplate, str]:
        """Carga templates predefinidas."""
        return {
            EmailTemplate.ORDER_CONFIRMATION: self._template_order_confirmation(),
            EmailTemplate.SHIPMENT_NOTIFICATION: self._template_shipment(),
            EmailTemplate.DELIVERY_CONFIRMATION: self._template_delivery(),
            EmailTemplate.PAYMENT_FAILED: self._template_payment_failed(),
            EmailTemplate.REFUND_NOTIFICATION: self._template_refund(),
            EmailTemplate.ACCOUNT_VERIFICATION: self._template_account_verification(),
        }

    def _template_order_confirmation(self) -> str:
        """Template: Confirmación de orden."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>¡Pedido Confirmado! 🎉</h2>
                <p>Hola {{customer_name}},</p>
                <p>Tu pedido ha sido confirmado exitosamente.</p>

                <h3>Detalles del Pedido</h3>
                <ul>
                    <li><strong>Número de Pedido:</strong> {{order_id}}</li>
                    <li><strong>Fecha:</strong> {{order_date}}</li>
                    <li><strong>Total:</strong> {{currency}} {{total_amount}}</li>
                </ul>

                <h3>Productos</h3>
                {{products_html}}

                <h3>Dirección de Envío</h3>
                <p>
                    {{shipping_address}}<br>
                    {{shipping_city}}, {{shipping_state}}<br>
                    {{shipping_country}}
                </p>

                <p><em>Recibirás una notificación cuando tu pedido sea despachado.</em></p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Si tienes preguntas, responde este email o contáctanos.
                </p>
            </body>
        </html>
        """

    def _template_shipment(self) -> str:
        """Template: Notificación de envío."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Tu Pedido Ha Sido Despachado 📦</h2>
                <p>Hola {{customer_name}},</p>
                <p>Excelente noticia: tu pedido ha sido despachado.</p>

                <h3>Información de Seguimiento</h3>
                <ul>
                    <li><strong>Número de Seguimiento:</strong> {{tracking_number}}</li>
                    <li><strong>Transportista:</strong> {{carrier_name}}</li>
                    <li><strong>Fecha Estimada de Entrega:</strong> {{estimated_delivery}}</li>
                </ul>

                <p>
                    <a href="{{tracking_url}}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Ver Seguimiento
                    </a>
                </p>

                <h3>Productos Enviados</h3>
                {{products_html}}

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Tracking actualizado cada 2-4 horas.
                </p>
            </body>
        </html>
        """

    def _template_delivery(self) -> str:
        """Template: Confirmación de entrega."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>¡Tu Pedido Ha Llegado! 🚀</h2>
                <p>Hola {{customer_name}},</p>
                <p>Tu pedido ha sido entregado exitosamente.</p>

                <h3>Detalles</h3>
                <ul>
                    <li><strong>Número de Pedido:</strong> {{order_id}}</li>
                    <li><strong>Fecha de Entrega:</strong> {{delivery_date}}</li>
                    <li><strong>Hora:</strong> {{delivery_time}}</li>
                </ul>

                <p><strong>¡Nos encantaría saber tu opinión!</strong></p>
                <p>
                    <a href="{{review_url}}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Dejar Reseña
                    </a>
                </p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Gracias por tu compra. ¡Esperamos verte pronto!
                </p>
            </body>
        </html>
        """

    def _template_payment_failed(self) -> str:
        """Template: Pago rechazado."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #d9534f;">
                <h2>⚠️ Problema con tu Pago</h2>
                <p>Hola {{customer_name}},</p>
                <p>No pudimos procesar tu pago.</p>

                <h3>Detalles</h3>
                <ul>
                    <li><strong>Número de Pedido:</strong> {{order_id}}</li>
                    <li><strong>Motivo:</strong> {{failure_reason}}</li>
                    <li><strong>Monto:</strong> {{currency}} {{amount}}</li>
                </ul>

                <p><strong>¿Qué hacer?</strong></p>
                <ol>
                    <li>Verifica que tu tarjeta tenga fondos</li>
                    <li>Intenta nuevamente con otro método de pago</li>
                    <li>Contacta a tu banco si el problema persiste</li>
                </ol>

                <p>
                    <a href="{{retry_payment_url}}" style="background-color: #d9534f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Reintentar Pago
                    </a>
                </p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Tu carrito se mantiene reservado por 24 horas.
                </p>
            </body>
        </html>
        """

    def _template_refund(self) -> str:
        """Template: Reembolso procesado."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #28a745;">
                <h2>✅ Reembolso Procesado</h2>
                <p>Hola {{customer_name}},</p>
                <p>Tu reembolso ha sido aprobado y procesado.</p>

                <h3>Detalles</h3>
                <ul>
                    <li><strong>Número de Pedido:</strong> {{order_id}}</li>
                    <li><strong>Monto del Reembolso:</strong> {{currency}} {{refund_amount}}</li>
                    <li><strong>Razón:</strong> {{refund_reason}}</li>
                    <li><strong>Estimado de Llegada:</strong> {{refund_eta}}</li>
                </ul>

                <p><em>El reembolso aparecerá en tu cuenta en 3-5 días hábiles.</em></p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Gracias por tu comprensión. Esperamos verte pronto.
                </p>
            </body>
        </html>
        """

    def _template_account_verification(self) -> str:
        """Template: Verificación de cuenta."""
        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Verifica tu Cuenta</h2>
                <p>Hola {{customer_name}},</p>
                <p>Para completar tu registro, verifica tu email haciendo clic en el botón:</p>

                <p style="margin: 20px 0;">
                    <a href="{{verification_url}}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Verificar Email
                    </a>
                </p>

                <p style="font-size: 12px; color: #999;">
                    O copia este enlace: {{verification_url}}
                </p>

                <hr>
                <p style="font-size: 12px; color: #999;">
                    Este enlace expira en 24 horas.
                </p>
            </body>
        </html>
        """

    def render(self, template: EmailTemplate, variables: Dict[str, Any]) -> str:
        """Renderiza template con variables."""
        html_content = self.templates.get(template)
        if not html_content:
            raise ValueError(f"Template {template.value} not found")

        # Escape HTML en valores de usuario
        safe_vars = {k: html.escape(str(v)) if isinstance(v, str) else v for k, v in variables.items()}

        # Render simple template (puede mejorarse con Jinja2)
        result = html_content
        for key, value in safe_vars.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))

        return result


class EmailService:
    """Servicio de notificaciones por email."""

    def __init__(self, provider: EmailProvider = EmailProvider.SENDGRID):
        self.provider = provider
        self.template_engine = EmailTemplateEngine()
        self._init_provider()

    def _init_provider(self) -> None:
        """Inicializa el proveedor de email."""
        if self.provider == EmailProvider.SENDGRID:
            self._init_sendgrid()
        elif self.provider == EmailProvider.AWS_SES:
            self._init_ses()
        elif self.provider == EmailProvider.SMTP:
            self._init_smtp()

    def _init_sendgrid(self) -> None:
        """Inicializa SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            api_key = os.getenv("SENDGRID_API_KEY")
            if not api_key:
                raise ValueError("SENDGRID_API_KEY not configured")
            self.sendgrid_client = SendGridAPIClient(api_key)
            logger.info("SendGrid initialized")
        except ImportError:
            logger.error("sendgrid package not installed")
            self.sendgrid_client = None

    def _init_ses(self) -> None:
        """Inicializa AWS SES."""
        try:
            import boto3
            self.ses_client = boto3.client("ses", region_name=os.getenv("AWS_REGION", "us-east-1"))
            logger.info("AWS SES initialized")
        except ImportError:
            logger.error("boto3 package not installed")
            self.ses_client = None

    def _init_smtp(self) -> None:
        """Inicializa SMTP."""
        self.smtp_config = {
            "host": os.getenv("SMTP_HOST", "localhost"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
        }
        logger.info(f"SMTP configured for {self.smtp_config['host']}")

    async def send_order_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: str,
        products: List[Dict[str, Any]],
        total_amount: float,
        currency: str = "USD",
        shipping_address: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Envía confirmación de orden."""

        products_html = self._render_products_html(products)
        shipping_addr = shipping_address or {}

        variables = {
            "customer_name": customer_name,
            "order_id": order_id,
            "order_date": datetime.utcnow().strftime("%d/%m/%Y"),
            "total_amount": f"{total_amount:.2f}",
            "currency": currency,
            "products_html": products_html,
            "shipping_address": shipping_addr.get("address", ""),
            "shipping_city": shipping_addr.get("city", ""),
            "shipping_state": shipping_addr.get("state", ""),
            "shipping_country": shipping_addr.get("country", ""),
        }

        html_content = self.template_engine.render(EmailTemplate.ORDER_CONFIRMATION, variables)

        message = EmailMessage(
            to=[EmailRecipient(email=customer_email, name=customer_name)],
            subject=f"Pedido Confirmado #{order_id}",
            html_content=html_content,
            metadata={"order_id": order_id, "type": "order_confirmation"},
        )

        return await self.send(message)

    async def send_shipment_notification(
        self,
        customer_email: str,
        customer_name: str,
        order_id: str,
        tracking_number: str,
        carrier_name: str,
        estimated_delivery: str,
        products: List[Dict[str, Any]],
        tracking_url: str = None,
    ) -> Dict[str, Any]:
        """Envía notificación de envío."""

        products_html = self._render_products_html(products)
        tracking_url = tracking_url or f"https://track.sellia.ai/{tracking_number}"

        variables = {
            "customer_name": customer_name,
            "order_id": order_id,
            "tracking_number": tracking_number,
            "carrier_name": carrier_name,
            "estimated_delivery": estimated_delivery,
            "products_html": products_html,
            "tracking_url": tracking_url,
        }

        html_content = self.template_engine.render(EmailTemplate.SHIPMENT_NOTIFICATION, variables)

        message = EmailMessage(
            to=[EmailRecipient(email=customer_email, name=customer_name)],
            subject=f"Tu Pedido Ha Sido Despachado - Seguimiento: {tracking_number}",
            html_content=html_content,
            metadata={"order_id": order_id, "tracking_number": tracking_number, "type": "shipment"},
        )

        return await self.send(message)

    async def send_payment_failed_alert(
        self,
        customer_email: str,
        customer_name: str,
        order_id: str,
        amount: float,
        currency: str,
        failure_reason: str,
        retry_url: str = None,
    ) -> Dict[str, Any]:
        """Envía alerta de pago rechazado."""

        retry_url = retry_url or f"https://checkout.sellia.ai/{order_id}"

        variables = {
            "customer_name": customer_name,
            "order_id": order_id,
            "failure_reason": failure_reason,
            "currency": currency,
            "amount": f"{amount:.2f}",
            "retry_payment_url": retry_url,
        }

        html_content = self.template_engine.render(EmailTemplate.PAYMENT_FAILED, variables)

        message = EmailMessage(
            to=[EmailRecipient(email=customer_email, name=customer_name)],
            subject="⚠️ Problema con tu Pago",
            html_content=html_content,
            metadata={"order_id": order_id, "type": "payment_failed"},
        )

        return await self.send(message)

    async def send_refund_notification(
        self,
        customer_email: str,
        customer_name: str,
        order_id: str,
        refund_amount: float,
        currency: str,
        refund_reason: str,
        refund_eta: str = "3-5 días hábiles",
    ) -> Dict[str, Any]:
        """Envía notificación de reembolso."""

        variables = {
            "customer_name": customer_name,
            "order_id": order_id,
            "refund_amount": f"{refund_amount:.2f}",
            "currency": currency,
            "refund_reason": refund_reason,
            "refund_eta": refund_eta,
        }

        html_content = self.template_engine.render(EmailTemplate.REFUND_NOTIFICATION, variables)

        message = EmailMessage(
            to=[EmailRecipient(email=customer_email, name=customer_name)],
            subject=f"✅ Reembolso Aprobado - ${refund_amount:.2f}",
            html_content=html_content,
            metadata={"order_id": order_id, "type": "refund", "amount": str(refund_amount)},
        )

        return await self.send(message)

    async def send(self, message: EmailMessage) -> Dict[str, Any]:
        """Envía email genérico."""

        logger.info(f"Sending email to {[r.email for r in message.to]}: {message.subject}")

        try:
            if self.provider == EmailProvider.SENDGRID:
                return await self._send_sendgrid(message)
            elif self.provider == EmailProvider.AWS_SES:
                return await self._send_ses(message)
            elif self.provider == EmailProvider.SMTP:
                return await self._send_smtp(message)
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_sendgrid(self, message: EmailMessage) -> Dict[str, Any]:
        """Envía via SendGrid."""
        if not self.sendgrid_client:
            return {"status": "error", "error": "SendGrid not configured"}

        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content

            mail = Mail(
                from_email=Email(message.from_email, message.from_name),
                to_emails=[To(r.email, r.name or r.email) for r in message.to],
                subject=message.subject,
                html_content=Content("text/html", message.html_content),
            )

            if message.cc:
                for cc_email in message.cc:
                    mail.add_cc(Email(cc_email))

            if message.bcc:
                for bcc_email in message.bcc:
                    mail.add_bcc(Email(bcc_email))

            response = self.sendgrid_client.send(mail)

            return {
                "status": "success",
                "message_id": response.headers.get("X-Message-ID"),
                "status_code": response.status_code,
            }

        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_ses(self, message: EmailMessage) -> Dict[str, Any]:
        """Envía via AWS SES."""
        if not self.ses_client:
            return {"status": "error", "error": "AWS SES not configured"}

        try:
            response = self.ses_client.send_email(
                Source=f"{message.from_name} <{message.from_email}>",
                Destination={
                    "ToAddresses": [r.email for r in message.to],
                    "CcAddresses": message.cc or [],
                    "BccAddresses": message.bcc or [],
                },
                Message={
                    "Subject": {"Data": message.subject},
                    "Body": {
                        "Html": {"Data": message.html_content},
                        "Text": {"Data": message.text_content or ""},
                    },
                },
            )

            return {
                "status": "success",
                "message_id": response.get("MessageId"),
            }

        except Exception as e:
            logger.error(f"AWS SES error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_smtp(self, message: EmailMessage) -> Dict[str, Any]:
        """Envía via SMTP."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{message.from_name} <{message.from_email}>"
            msg["To"] = ", ".join([r.email for r in message.to])

            if message.text_content:
                msg.attach(MIMEText(message.text_content, "plain"))
            msg.attach(MIMEText(message.html_content, "html"))

            async with aiosmtplib.SMTP(
                hostname=self.smtp_config["host"],
                port=self.smtp_config["port"],
            ) as smtp:
                if self.smtp_config["user"]:
                    await smtp.login(self.smtp_config["user"], self.smtp_config["password"])

                await smtp.send_message(msg)

            return {"status": "success", "message": "Email sent via SMTP"}

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _render_products_html(self, products: List[Dict[str, Any]]) -> str:
        """Renderiza lista de productos en HTML."""
        html = "<ul>"
        for product in products:
            html += f"""
            <li>
                <strong>{html.escape(product.get('name', 'Producto'))}</strong><br>
                Cantidad: {product.get('quantity', 1)} |
                Precio: {product.get('currency', 'USD')} {product.get('price', 0):.2f}
            </li>
            """
        html += "</ul>"
        return html
