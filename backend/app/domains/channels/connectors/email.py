import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class EmailConnector(BaseChannelConnector):
    platform = "email"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.smtp_host = credentials.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = credentials.get("smtp_port", 587)
        self.smtp_user = credentials.get("smtp_user")
        self.smtp_password = credentials.get("smtp_password")
        self.from_address = credentials.get("from_address") or self.smtp_user

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text", subject: str = None) -> dict[str, Any]:
        if not self.smtp_user or not self.smtp_password:
            raise ValueError("Faltan credenciales SMTP")

        msg = MIMEMultipart()
        msg["From"] = self.from_address
        msg["To"] = recipient_id
        if subject:
            msg["Subject"] = subject
        else:
            msg["Subject"] = self.settings.get("subject_prefix", "[Agente IA]") + " Nuevo mensaje"

        body = MIMEText(content, "plain", "utf-8")
        msg.attach(body)

        await aiosmtplib.send(
            msg,
            hostname=self.smtp_host,
            port=self.smtp_port,
            start_tls=True,
            username=self.smtp_user,
            password=self.smtp_password,
            timeout=30,
        )
        return {"status": "sent", "recipient": recipient_id}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        return WebhookPayload(
            platform=ChannelPlatform.EMAIL,
            external_id=raw_payload.get("from"),
            sender_name=raw_payload.get("from_name"),
            sender_email=raw_payload.get("from"),
            content=raw_payload.get("body", ""),
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.smtp_user or not self.smtp_password:
            return False
        try:
            await aiosmtplib.connect(
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_user,
                password=self.smtp_password,
                timeout=10,
            )
            return True
        except Exception:
            return False
