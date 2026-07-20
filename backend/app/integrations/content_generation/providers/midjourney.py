"""Midjourney Provider — AI Art Generation

Pricing: ~$0.05/image (via API proxy como imagineapi.dev o midjourney-api.com)
Strengths: Aesthetic quality, artistic style, community trends
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()


class MidjourneyProvider(BaseProvider):
    """Proveedor de imágenes artísticas usando Midjourney API proxy."""

    name = "Midjourney"
    slug = "midjourney"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.MIDJOURNEY_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.05 * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {"midjourney-standard": 0.05, "midjourney-hd": 0.08}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="MIDJOURNEY_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.MIDJOURNEY_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
            }
            if config.aspect_ratio:
                payload["aspect_ratio"] = config.aspect_ratio

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.imagineapi.dev/items/images",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            image_id = data.get("data", {}).get("id")
            if not image_id:
                return GenerationResult(success=False, error_message="Midjourney no devolvió ID")

            # Poll
            image_url = None
            for _ in range(60):
                import asyncio
                await asyncio.sleep(5)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.imagineapi.dev/items/images/{image_id}",
                        headers=headers,
                    ) as poll_resp:
                        poll_data = await poll_resp.json()
                        status = poll_data.get("data", {}).get("status")
                        if status == "completed":
                            image_url = poll_data.get("data", {}).get("url")
                            break
                        elif status == "failed":
                            return GenerationResult(success=False, error_message="Midjourney generation failed")

            if not image_url:
                return GenerationResult(success=False, error_message="Midjourney timeout")

            image_bytes = await download_url(image_url)
            compressed = None
            if image_bytes:
                compressed = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=0.05,
                model_used="midjourney-v6",
                quality_tier=config.quality,
                metadata={"image_id": image_id},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
