"""Opus Clip Provider — Video Repurposing

Pricing: ~$0.05/minute
Strengths: Converts long videos into viral shorts, auto-captions, AI hooks
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class OpusClipProvider(BaseProvider):
    """Proveedor de repurposing de video usando Opus Clip API."""

    name = "Opus Clip"
    slug = "opusclip"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.OPUSCLIP_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 60
        return 0.05 * (duration / 60)

    def get_pricing_table(self) -> Dict[str, float]:
        return {"opusclip-repurpose": 0.05}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="OPUSCLIP_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.OPUSCLIP_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "video_url": config.reference_image_url or config.extra_params.get("video_url", ""),
                "prompt": config.prompt,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.opus.pro/v1/clip",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            clips = data.get("clips", [])
            if not clips:
                return GenerationResult(success=False, error_message="Opus Clip no devolvió clips")

            video_url = clips[0].get("url")
            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=self.estimate_cost(config),
                model_used="opusclip-ai",
                quality_tier=config.quality,
                duration_seconds=config.duration_seconds,
                metadata={"clips_count": len(clips)},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
