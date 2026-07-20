"""Luma Dream Machine Provider — 3D/NeRF Video

Pricing: ~$0.05/second (via fal.ai)
Strengths: 3D video, NeRF, product visualization
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class LumaProvider(BaseProvider):
    """Proveedor de video 3D usando Luma Dream Machine via fal.ai."""

    name = "Luma Dream Machine"
    slug = "luma"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.FAL_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 5
        return 0.05 * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {"luma-dream-machine": 0.05}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="FAL_KEY no configurada para Luma")

        try:
            import fal_client
            fal_client.api_key = settings.FAL_KEY

            result = await fal_client.subscribe_async(
                "fal-ai/luma-dream-machine",
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
                return GenerationResult(success=False, error_message="Luma no devolvió video")

            duration = config.duration_seconds or 5
            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=self.estimate_cost(config),
                model_used="luma-dream-machine",
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
