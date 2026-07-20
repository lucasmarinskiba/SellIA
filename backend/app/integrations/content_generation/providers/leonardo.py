"""Leonardo.ai Provider — AI Image Generation

Pricing: ~$0.015/image (via API credits)
Strengths: Artistic quality, Alchemy, photo-real, fine-tuned models
"""

from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()

LEONARDO_COSTS = {
    ContentQuality.DRAFT: 0.012,
    ContentQuality.STANDARD: 0.015,
    ContentQuality.PREMIUM: 0.025,
}


class LeonardoProvider(BaseProvider):
    """Proveedor de imágenes usando Leonardo.ai API."""

    name = "Leonardo.ai"
    slug = "leonardo"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.LEONARDO_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        cost = LEONARDO_COSTS.get(config.quality, LEONARDO_COSTS[ContentQuality.STANDARD])
        return cost * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "leonardo-standard": 0.015,
            "leonardo-alchemy": 0.025,
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="LEONARDO_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.LEONARDO_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
                "num_images": config.num_variations,
                "width": config.width or 1024,
                "height": config.height or 1024,
            }

            if config.negative_prompt:
                payload["negative_prompt"] = config.negative_prompt

            # Alchemy para premium
            if config.quality == ContentQuality.PREMIUM:
                payload["alchemy"] = True
                payload["photoReal"] = True

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://cloud.leonardo.ai/api/rest/v1/generations",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            generation_id = data.get("sdGenerationJob", {}).get("generationId")
            if not generation_id:
                return GenerationResult(success=False, error_message="Leonardo no devolvió generationId")

            # Poll for result
            image_url = None
            for _ in range(30):
                import asyncio
                await asyncio.sleep(2)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers,
                    ) as poll_resp:
                        poll_data = await poll_resp.json()
                        images = poll_data.get("generations_by_pk", {}).get("generated_images", [])
                        if images:
                            image_url = images[0].get("url")
                            break

            if not image_url:
                return GenerationResult(success=False, error_message="Leonardo timeout")

            # Download and compress
            image_bytes = await download_url(image_url)
            compressed = None
            if image_bytes:
                compressed = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))

            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=cost,
                model_used="leonardo-phoenix" if config.quality == ContentQuality.PREMIUM else "leonardo-default",
                quality_tier=config.quality,
                width=config.width or 1024,
                height=config.height or 1024,
                metadata={"generation_id": generation_id},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
