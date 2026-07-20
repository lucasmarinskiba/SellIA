"""Seedance 2.0 Provider — ByteDance Video Generation via fal.ai

Pricing (2026):
- Seedance 2.0 Standard: ~$0.10/segundo
- Seedance 2.0 Fast: ~$0.081/segundo (~19% más barato)
- Soporta text-to-video, image-to-video, audio-to-video
- Resoluciones: 480p, 720p, 1080p
- Duraciones: 3s, 5s, 8s, 10s

Nuestro proveedor premium de video. Se usa cuando la calidad es prioridad.
"""

from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url

settings = get_settings()

# fal.ai endpoints para Seedance
SEEDANCE_ENDPOINTS = {
    "text-to-video": "fal-ai/seedance/seedance-2-pro/text-to-video",
    "image-to-video": "fal-ai/seedance/seedance-2-pro/image-to-video",
    "fast": "fal-ai/seedance/seedance-2-fast/text-to-video",
}

# Costos por segundo
SEEDANCE_COSTS = {
    ContentQuality.DRAFT: 0.081,   # Fast tier
    ContentQuality.STANDARD: 0.10,  # Standard tier
    ContentQuality.PREMIUM: 0.12,   # Standard con 1080p
}

DURATIONS = [3, 5, 8, 10]
RESOLUTIONS = ["480p", "720p", "1080p"]


class SeedanceProvider(BaseProvider):
    """Proveedor de video usando Seedance 2.0 via fal.ai."""

    name = "Seedance 2.0"
    slug = "seedance"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        # fal.ai usa FAL_KEY
        return bool(getattr(settings, "FAL_KEY", None))

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 5
        # Ajustar a duración permitida
        duration = min(DURATIONS, key=lambda x: abs(x - duration))
        cost_per_sec = SEEDANCE_COSTS.get(config.quality, SEEDANCE_COSTS[ContentQuality.STANDARD])
        return cost_per_sec * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "seedance-fast": 0.081,
            "seedance-standard": 0.10,
            "seedance-premium": 0.12,
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="FAL_KEY no configurada. Seedance requiere API key de fal.ai",
            )

        try:
            import fal_client

            fal_client.api_key = settings.FAL_KEY

            duration = config.duration_seconds or 5
            duration = min(DURATIONS, key=lambda x: abs(x - duration))

            resolution = config.extra_params.get("resolution", "720p")
            if resolution not in RESOLUTIONS:
                resolution = "720p"

            aspect_ratio = config.aspect_ratio or "16:9"

            # Seleccionar endpoint
            if config.quality == ContentQuality.DRAFT:
                endpoint = SEEDANCE_ENDPOINTS["fast"]
            elif config.reference_image_url:
                endpoint = SEEDANCE_ENDPOINTS["image-to-video"]
            else:
                endpoint = SEEDANCE_ENDPOINTS["text-to-video"]

            arguments = {
                "prompt": config.prompt,
                "duration": str(duration),
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
            }

            if config.reference_image_url:
                arguments["image_url"] = config.reference_image_url

            if config.extra_params.get("generate_audio", False):
                arguments["generate_audio"] = True

            # Usar fal.subscribe para esperar resultado
            result = await fal_client.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=False,
            )

            video_url = None
            if hasattr(result, "video") and result.video:
                video_url = result.video.url
            elif isinstance(result, dict):
                video_url = result.get("video", {}).get("url") if isinstance(result.get("video"), dict) else result.get("video")

            if not video_url:
                return GenerationResult(
                    success=False,
                    error_message="Seedance no devolvió URL de video",
                    metadata={"raw_result": str(result)},
                )

            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=cost,
                model_used="seedance-2-pro" if config.quality != ContentQuality.DRAFT else "seedance-2-fast",
                quality_tier=config.quality,
                duration_seconds=duration,
                width=1920 if resolution == "1080p" else 1280 if resolution == "720p" else 854,
                height=1080 if resolution == "1080p" else 720 if resolution == "720p" else 480,
                metadata={
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "generate_audio": arguments.get("generate_audio", False),
                },
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )
