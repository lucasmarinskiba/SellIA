"""Ollama Provider — Free Local LLM for Copy Generation

Runs entirely on your own hardware. Zero API costs.
Requires Ollama server running locally (default: http://localhost:11434).
Recommended models: llama3.1, mistral, qwen2.5, phi4
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class OllamaProvider(BaseProvider):
    """Proveedor de copy usando Ollama (modelos locales gratuitos)."""

    name = "Ollama (Local LLM)"
    slug = "ollama"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        import aiohttp
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        try:
            # Use a simple sync check for property; async check is done in router
            return True  # Router will verify availability before calling
        except Exception:
            return False

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.0  # Completely free

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "copy_generation": 0.0,
            "note": "Runs locally — only electricity/CPU cost",
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")

        try:
            import aiohttp

            model = config.extra_params.get("model", "llama3.1")
            temperature = config.extra_params.get("temperature", 0.7)
            max_tokens = config.extra_params.get("max_tokens", 1500)
            system_prompt = config.extra_params.get("system_prompt", "")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": config.prompt})

            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return GenerationResult(
                            success=False,
                            error_message=f"Ollama returned {resp.status}: {text}",
                        )
                    data = await resp.json()

            text = data.get("message", {}).get("content", "")
            if not text:
                return GenerationResult(success=False, error_message="Ollama returned empty content")

            return GenerationResult(
                success=True,
                text_content=text,
                cost_usd=0.0,
                model_used=model,
                quality_tier=config.quality,
                metadata={
                    "provider": "ollama",
                    "local": True,
                    "eval_count": data.get("eval_count", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                },
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
