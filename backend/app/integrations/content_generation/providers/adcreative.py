"""AdCreative.ai Provider — AI Ad Banners

Pricing: Plan-based, ~$0.10/creative
Strengths: Meta Ads, Google Ads, TikTok Ads optimized creatives
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()


class AdCreativeProvider(BaseProvider):
    """Proveedor de creativos de ads usando AdCreative.ai API."""

    name = "AdCreative.ai"
    slug = "adcreative"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.ADCREATIVE_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.10 * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {"adcreative-banner": 0.10}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="ADCREATIVE_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.ADCREATIVE_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "description": config.prompt,
                "target": config.extra_params.get("target", "conversion"),
                "size": config.extra_params.get("size", "1080x1080"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.adcreative.ai/v1/creatives",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            image_url = data.get("creative", {}).get("url") if isinstance(data.get("creative"), dict) else data.get("url")
            if not image_url:
                return GenerationResult(success=False, error_message="AdCreative no devolvió creative")

            image_bytes = await download_url(image_url)
            compressed = None
            if image_bytes:
                compressed = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=0.10,
                model_used="adcreative-ai",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
