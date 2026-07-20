from abc import ABC, abstractmethod
from typing import Any

from app.domains.channels.schemas import WebhookPayload


class BaseChannelConnector(ABC):
    platform: str

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        self.credentials = credentials
        self.settings = settings

    @abstractmethod
    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Envía un mensaje al destinatario."""
        pass

    @abstractmethod
    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Convierte el payload raw del webhook en un WebhookPayload estandarizado."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Valida que las credenciales sean correctas."""
        pass
