"""Base Provider Interface for Computer Use Agents."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.domains.computer_use.schemas import ComputerUseAction


class ComputerUseProvider(ABC):
    """Interfaz abstracta para proveedores de visión de Computer Use."""

    provider_name: str = "base"
    supports_vision: bool = True

    @abstractmethod
    async def decide_action(
        self,
        screenshot_bytes: bytes,
        task: str,
        history: List[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        page_info: Optional[Dict[str, str]] = None,
    ) -> ComputerUseAction:
        """Decide la próxima acción basada en el screenshot actual.

        Returns:
            ComputerUseAction con action_type, params y reason.
        """
        pass

    @abstractmethod
    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        """Genera un resumen de la sesión basado en el log de acciones."""
        pass

    def _encode_image(self, image_bytes: bytes) -> str:
        """Codifica imagen a base64."""
        import base64
        return base64.b64encode(image_bytes).decode("utf-8")
