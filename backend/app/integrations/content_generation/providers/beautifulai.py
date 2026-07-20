"""Beautiful.ai Provider — AI Presentations

Pricing: Plan-based, ~$0.05/slide
Strengths: Auto-layout, smart templates, professional decks
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class BeautifulAIProvider(BaseProvider):
    """Proveedor de presentaciones usando Beautiful.ai API."""

    name = "Beautiful.ai"
    slug = "beautifulai"
    supports = [ContentType.COPY]  # Genera presentaciones, pero usamos COPY como proxy

    @property
    def is_available(self) -> bool:
        return bool(settings.BEAUTIFULAI_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.05

    def get_pricing_table(self) -> Dict[str, float]:
        return {"beautifulai-slide": 0.05}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="BEAUTIFULAI_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.BEAUTIFULAI_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "title": config.prompt[:100],
                "description": config.prompt,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.beautiful.ai/v1/presentations",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            deck_url = data.get("url") or data.get("presentation", {}).get("url")
            if not deck_url:
                return GenerationResult(success=False, error_message="Beautiful.ai no devolvió presentación")

            return GenerationResult(
                success=True,
                url=deck_url,
                cost_usd=0.05,
                model_used="beautifulai-v2",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
