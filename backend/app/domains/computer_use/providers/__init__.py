"""Computer Use Providers

Proveedores de IA con capacidades de visión para Computer Use Agents.
Soporta múltiples backends: OpenAI GPT-4o, Anthropic Claude (nativo), Ollama local.
"""

from .base import ComputerUseProvider
from .factory import create_provider_with_fallback

__all__ = ["ComputerUseProvider", "create_provider_with_fallback"]
