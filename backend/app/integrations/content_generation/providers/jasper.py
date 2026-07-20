"""Jasper Provider — Long-Form Copy Generation

Pricing: ~$0.01/generation
Strengths: Emails, sequences, blog posts, brand voice consistency
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class JasperProvider(BaseProvider):
    """Proveedor de copy largo usando Jasper API."""

    name = "Jasper"
    slug = "jasper"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        return bool(settings.JASPER_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.01

    def get_pricing_table(self) -> Dict[str, float]:
        return {"jasper-generation": 0.01}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="JASPER_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.JASPER_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
                "language": config.extra_params.get("language", "es"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.jasper.ai/v1/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            text = data.get("text") or data.get("content")
            if not text:
                return GenerationResult(success=False, error_message="Jasper no devolvió texto")

            return GenerationResult(
                success=True,
                text_content=text,
                cost_usd=0.01,
                model_used="jasper-boss-mode",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
