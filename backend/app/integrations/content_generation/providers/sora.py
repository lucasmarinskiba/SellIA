"""Sora Provider — OpenAI Video Generation

Pricing: ~$0.20-$0.50/second (estimated)
Strengths: Photorealism, physics, narrative video
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class SoraProvider(BaseProvider):
    """Proveedor de video generativo usando OpenAI Sora."""

    name = "Sora (OpenAI)"
    slug = "sora"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 5
        return 0.30 * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {"sora-standard": 0.30, "sora-hd": 0.50}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="OPENAI_API_KEY no configurada para Sora")

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            # Sora API (when publicly available)
            response = await client.videos.generate(
                model="sora",
                prompt=config.prompt,
                duration=config.duration_seconds or 5,
                aspect_ratio=config.aspect_ratio or "16:9",
            )

            video_url = response.data[0].url if response.data else None
            if not video_url:
                return GenerationResult(success=False, error_message="Sora no devolvió video")

            duration = config.duration_seconds or 5
            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=self.estimate_cost(config),
                model_used="sora-1",
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
