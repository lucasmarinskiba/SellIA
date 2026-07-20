"""Kling AI Provider — Realistic Physics Video

Pricing: ~$0.06/second (via fal.ai)
Strengths: Real-world physics, human motion, realistic scenes
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class KlingProvider(BaseProvider):
    """Proveedor de video con física realista usando Kling AI via fal.ai."""

    name = "Kling AI"
    slug = "kling"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.FAL_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 5
        return 0.06 * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {"kling-video": 0.06}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="FAL_KEY no configurada para Kling")

        try:
            import fal_client
            fal_client.api_key = settings.FAL_KEY

            result = await fal_client.subscribe_async(
                "fal-ai/kling-video/v1/standard/text-to-video",
                arguments={
                    "prompt": config.prompt,
                    "duration": str(min(config.duration_seconds or 5, 10)),
                },
            )

            video_url = None
            if hasattr(result, "video") and result.video:
                video_url = result.video.url
            elif isinstance(result, dict):
                video_url = result.get("video", {}).get("url") if isinstance(result.get("video"), dict) else result.get("video")

            if not video_url:
                return GenerationResult(success=False, error_message="Kling no devolvió video")

            duration = config.duration_seconds or 5
            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=self.estimate_cost(config),
                model_used="kling-v1",
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
