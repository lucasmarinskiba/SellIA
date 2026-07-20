"""Copy.ai Provider — Marketing Copy Generation

Pricing: ~$0.005/generation
Strengths: Ads, headlines, social captions, quick marketing copy
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class CopyAIProvider(BaseProvider):
    """Proveedor de copy de marketing usando Copy.ai API."""

    name = "Copy.ai"
    slug = "copyai"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        return bool(settings.COPYAI_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.005

    def get_pricing_table(self) -> Dict[str, float]:
        return {"copyai-generation": 0.005}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="COPYAI_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "x-api-key": settings.COPYAI_API_KEY,
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
                "tone": config.extra_params.get("tone", "friendly"),
                "language": config.extra_params.get("language", "es"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.copy.ai/api/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            text = data.get("data", {}).get("text") if isinstance(data.get("data"), dict) else data.get("text")
            if not text:
                return GenerationResult(success=False, error_message="Copy.ai no devolvió texto")

            return GenerationResult(
                success=True,
                text_content=text,
                cost_usd=0.005,
                model_used="copyai-gpt4",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
