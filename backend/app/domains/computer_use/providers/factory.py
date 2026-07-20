"""Factory para crear providers de Computer Use con fallback automático.

Orden de preferencia:
1. Anthropic Native Computer Use API (más preciso para coordenadas)
2. OpenAI GPT-4o (excelente visión, formato JSON)
3. Ollama local (gratis, privado, menos preciso)
"""

from typing import Optional, List, Dict, Any

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.schemas import ComputerUseAction
from .base import ComputerUseProvider

logger = get_logger(__name__)

# Provider priority order
PROVIDER_PRIORITY = [
    ("anthropic_native", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("ollama", None),  # No key needed, checks availability
]


async def _is_ollama_available() -> bool:
    """Check if Ollama server is reachable and has a vision model."""
    from app.core.config import get_settings
    base_url = get_settings().OLLAMA_BASE_URL.rstrip("/")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                models = data.get("models", [])
                # Check if any vision model is available
                vision_models = ["llava", "bakllava", "moondream", "llava-phi3"]
                return any(
                    any(vm in m.get("name", "").lower() for vm in vision_models)
                    for m in models
                )
    except Exception:
        return False


def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
) -> Optional[ComputerUseProvider]:
    """Crea un provider específico.

    Args:
        provider_name: "anthropic_native", "openai", "ollama"
        api_key: API key para el provider (no necesaria para Ollama)

    Returns:
        Instancia del provider o None si no se puede crear.
    """
    settings = get_settings()

    if provider_name == "anthropic_native":
        key = api_key or settings.ANTHROPIC_API_KEY
        if not key:
            return None
        try:
            from .anthropic_native import AnthropicNativeProvider
            return AnthropicNativeProvider(api_key=key)
        except ImportError as e:
            logger.warning(f"Anthropic native provider not available: {e}")
            return None

    elif provider_name == "openai":
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            return None
        from .openai_vision import OpenAIVisionProvider
        return OpenAIVisionProvider(api_key=key)

    elif provider_name == "ollama":
        from .ollama_vision import OllamaVisionProvider
        return OllamaVisionProvider()

    else:
        logger.warning(f"Unknown provider: {provider_name}")
        return None


async def create_provider_with_fallback(
    preferred_provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ComputerUseProvider:
    """Crea un provider con fallback automático.

    Intenta el provider preferido, luego recorre la lista de prioridad.
    Si nada funciona, lanza excepción.

    Args:
        preferred_provider: Nombre del provider preferido (opcional)
        api_key: API key específica (opcional)

    Returns:
        ComputerUseProvider listo para usar

    Raises:
        RuntimeError: Si ningún provider está disponible
    """
    settings = get_settings()

    # If preferred provider specified, try it first
    if preferred_provider:
        provider = create_provider(preferred_provider, api_key)
        if provider:
            logger.info(f"Using preferred Computer Use provider: {preferred_provider}")
            return provider
        logger.warning(f"Preferred provider {preferred_provider} not available, trying fallback...")

    # Try each provider in priority order
    for provider_name, env_key in PROVIDER_PRIORITY:
        if provider_name == preferred_provider:
            continue  # Already tried

        # Special check for Ollama
        if provider_name == "ollama":
            if await _is_ollama_available():
                provider = create_provider("ollama")
                if provider:
                    logger.info("Using Ollama local provider for Computer Use")
                    return provider
            continue

        # Check if API key is available
        key = api_key if env_key and api_key else getattr(settings, env_key, None) if env_key else None
        if not key:
            continue

        provider = create_provider(provider_name, key)
        if provider:
            logger.info(f"Using Computer Use provider: {provider_name}")
            return provider

    raise RuntimeError(
        "No Computer Use provider available. "
        "Please configure OPENAI_API_KEY, ANTHROPIC_API_KEY, or run Ollama with a vision model."
    )


class FallbackComputerUseProvider(ComputerUseProvider):
    """Wrapper que maneja fallback entre providers en tiempo de ejecución.

    Si un provider falla durante decide_action, intenta el siguiente.
    """

    provider_name = "fallback"
    supports_vision = True

    def __init__(self, providers: list[ComputerUseProvider]):
        self.providers = providers
        self.current_index = 0

    async def decide_action(
        self,
        screenshot_bytes: bytes,
        task: str,
        history: List[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        page_info: Optional[Dict[str, str]] = None,
    ) -> ComputerUseAction:
        errors = []

        for i, provider in enumerate(self.providers):
            try:
                result = await provider.decide_action(
                    screenshot_bytes, task, history, user_message, page_info
                )
                # If this provider succeeded, prefer it next time
                if result.action_type != "error":
                    self.current_index = i
                    return result
                errors.append(f"{provider.provider_name}: {result.params.get('message', 'error')}")
            except Exception as e:
                errors.append(f"{provider.provider_name}: {str(e)}")
                continue

        # All providers failed
        return ComputerUseAction(
            action_type="error",
            params={"message": f"All providers failed: {'; '.join(errors)}"},
            reason="All providers failed",
        )

    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        for provider in self.providers:
            try:
                return await provider.generate_summary(actions_log)
            except Exception:
                continue
        return "Sesión completada."
