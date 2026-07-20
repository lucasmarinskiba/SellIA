"""Computer Use — Vision Agent (Legacy Wrapper)

Este módulo ahora es un wrapper sobre el sistema de providers.
Mantiene compatibilidad hacia atrás mientras delega todo al factory.

Los providers están en app/domains/computer_use/providers/:
- anthropic_native.py: API nativa de Claude Computer Use (beta)
- openai_vision.py: GPT-4o con visión + JSON
- ollama_vision.py: Ollama local (llava, bakllava, etc.)
- factory.py: Creación con fallback automático
"""

from typing import Optional, List, Dict, Any

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.providers.factory import create_provider_with_fallback, FallbackComputerUseProvider
from app.domains.computer_use.providers.base import ComputerUseProvider

logger = get_logger(__name__)


class VisionAgent:
    """Agente de visión que decide acciones basadas en screenshots.

    Delega a un provider con fallback automático.
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "auto"):
        self.api_key = api_key
        self.provider_name = provider  # "auto", "anthropic_native", "openai", "ollama"
        self.settings = get_settings()
        self._provider: Optional[ComputerUseProvider] = None

    async def _get_provider(self) -> ComputerUseProvider:
        """Obtiene o crea el provider con fallback."""
        if self._provider is None:
            preferred = None if self.provider_name == "auto" else self.provider_name
            self._provider = await create_provider_with_fallback(
                preferred_provider=preferred,
                api_key=self.api_key,
            )
        return self._provider

    async def decide_action(
        self,
        screenshot_bytes: bytes,
        task: str,
        history: List[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        page_info: Optional[Dict[str, str]] = None,
    ) -> ComputerUseAction:
        """Decide la próxima acción basada en el screenshot actual."""
        if history is None:
            history = []

        try:
            provider = await self._get_provider()
            return await provider.decide_action(
                screenshot_bytes=screenshot_bytes,
                task=task,
                history=history,
                user_message=user_message,
                page_info=page_info,
            )
        except Exception as e:
            logger.error(f"VisionAgent failed: {e}")
            return ComputerUseAction(
                action_type="error",
                params={"message": str(e)[:200]},
                reason="VisionAgent error",
            )

    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        """Genera un resumen de la sesión."""
        try:
            provider = await self._get_provider()
            return await provider.generate_summary(actions_log)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Sesión completada."
