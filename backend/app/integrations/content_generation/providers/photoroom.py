"""Photoroom Provider — Product Photo Generation & Background Removal

Pricing: ~$0.02/image
Strengths: Background removal, product photography, batch editing
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()


class PhotoroomProvider(BaseProvider):
    """Proveedor de fotos de producto usando Photoroom API."""

    name = "Photoroom"
    slug = "photoroom"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.PHOTOROOM_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.02 * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {"photoroom-generate": 0.02, "photoroom-remove-bg": 0.01}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="PHOTOROOM_API_KEY no configurada")

        try:
            import aiohttp

            headers = {"x-api-key": settings.PHOTOROOM_API_KEY}

            # Photoroom Generate API
            payload = {
                "prompt": config.prompt,
                "num_images": config.num_variations,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://sdk.photoroom.com/v1/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            image_url = data.get("image", {}).get("url") if isinstance(data.get("image"), dict) else data.get("images", [{}])[0].get("url")
            if not image_url:
                return GenerationResult(success=False, error_message="Photoroom no devolvió imagen")

            image_bytes = await download_url(image_url)
            compressed = None
            if image_bytes:
                compressed = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=0.02,
                model_used="photoroom-generate",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
