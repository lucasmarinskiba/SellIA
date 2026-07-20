"""Ideogram Provider — Text-in-Image Generation

Pricing: ~$0.04/image
Strengths: Typography, text rendering, logos, posters
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()


class IdeogramProvider(BaseProvider):
    """Proveedor de imágenes con texto usando Ideogram API."""

    name = "Ideogram 2.0"
    slug = "ideogram"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.IDEOGRAM_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.04 * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {"ideogram-v2": 0.04}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="IDEOGRAM_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Api-Key": settings.IDEOGRAM_API_KEY,
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
                "aspect_ratio": config.aspect_ratio or "1:1",
                "model": "V_2",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.ideogram.ai/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            images = data.get("data", [])
            if not images:
                return GenerationResult(success=False, error_message="Ideogram no devolvió imagen")

            image_url = images[0].get("url")
            image_bytes = await download_url(image_url)
            compressed = None
            if image_bytes:
                compressed = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=0.04,
                model_used="ideogram-v2",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
