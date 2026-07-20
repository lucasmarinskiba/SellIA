"""Runway Provider — Gen-4 / Gen-3 Video Generation

Pricing (2025-2026):
- Gen-4 Turbo: 5 credits/seg = $0.05/seg
- Gen-4 Standard: 12 credits/seg = $0.12/seg
- Gen-3 Alpha Turbo: 5 credits/seg = $0.05/seg
- Gen-3 Alpha: 10 credits/seg = $0.10/seg
- Upscale 4K: +2 credits/seg

Usamos Gen-4 Turbo para drafts (rápido y económico),
Gen-4 Standard para producción.
"""

import asyncio
from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url

settings = get_settings()

# Modelos Runway por calidad
RUNWAY_MODELS = {
    ContentQuality.DRAFT: {
        "model": "gen-4-turbo",
        "cost_per_second": 0.05,
    },
    ContentQuality.STANDARD: {
        "model": "gen-4",
        "cost_per_second": 0.12,
    },
    ContentQuality.PREMIUM: {
        "model": "gen-4",
        "cost_per_second": 0.14,  # + upscale
    },
}

ASPECT_RATIOS = {
    "16:9": "1920:1080",
    "9:16": "1080:1920",
    "1:1": "1080:1080",
    "4:3": "1440:1080",
    "3:4": "1080:1440",
}


class RunwayProvider(BaseProvider):
    """Proveedor de video usando Runway ML API."""

    name = "Runway ML"
    slug = "runway"
    supports = [ContentType.VIDEO, ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.RUNWAY_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        if config.content_type == ContentType.VIDEO:
            duration = config.duration_seconds or 5
            model_config = RUNWAY_MODELS.get(config.quality, RUNWAY_MODELS[ContentQuality.STANDARD])
            cost = model_config["cost_per_second"] * duration
            if config.quality == ContentQuality.PREMIUM:
                cost += 0.02 * duration  # upscale
            return cost
        elif config.content_type == ContentType.IMAGE:
            # Gen-4 image: ~5-8 credits
            return 0.05
        return 0.0

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "gen-4-turbo": 0.05,
            "gen-4": 0.12,
            "gen-4-upscale": 0.14,
            "gen-3-alpha-turbo": 0.05,
            "gen-3-alpha": 0.10,
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="RUNWAY_API_KEY no configurada",
            )

        try:
            if config.content_type == ContentType.VIDEO:
                return await self._generate_video(config)
            elif config.content_type == ContentType.IMAGE:
                return await self._generate_image(config)
            else:
                return GenerationResult(
                    success=False,
                    error_message=f"Tipo {config.content_type.value} no soportado por Runway",
                )
        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )

    async def _generate_video(self, config: GenerationConfig) -> GenerationResult:
        model_config = RUNWAY_MODELS.get(config.quality, RUNWAY_MODELS[ContentQuality.STANDARD])
        duration = min(config.duration_seconds or 5, 10)  # Max 10s base

        # Runway API REST
        import aiohttp

        headers = {
            "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": config.prompt,
            "model": model_config["model"],
            "duration": duration,
        }

        # Aspect ratio
        if config.aspect_ratio:
            payload["ratio"] = ASPECT_RATIOS.get(config.aspect_ratio, "16:9")

        # Image-to-video
        if config.reference_image_url:
            payload["image_url"] = config.reference_image_url

        # Seed
        if config.seed is not None:
            payload["seed"] = config.seed

        async with aiohttp.ClientSession() as session:
            # 1. Crear tarea
            async with session.post(
                "https://api.dev.runwayml.com/v1/generations",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status not in (200, 201, 202):
                    text = await resp.text()
                    return GenerationResult(
                        success=False,
                        error_message=f"Runway API error {resp.status}: {text}",
                    )
                data = await resp.json()
                task_id = data.get("id")

            if not task_id:
                return GenerationResult(
                    success=False,
                    error_message="Runway no devolvió task ID",
                )

            # 2. Poll hasta completar
            video_url = None
            max_attempts = 60
            for _ in range(max_attempts):
                await asyncio.sleep(2)
                async with session.get(
                    f"https://api.dev.runwayml.com/v1/generations/{task_id}",
                    headers=headers,
                ) as poll_resp:
                    poll_data = await poll_resp.json()
                    status = poll_data.get("status")
                    if status == "succeeded":
                        video_url = poll_data.get("output", [{}])[0].get("url")
                        break
                    elif status in ("failed", "error"):
                        return GenerationResult(
                            success=False,
                            error_message=f"Runway generation failed: {poll_data.get('error', 'Unknown')}",
                        )

            if not video_url:
                return GenerationResult(
                    success=False,
                    error_message="Runway timeout esperando video",
                )

            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=cost,
                model_used=model_config["model"],
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={
                    "task_id": task_id,
                    "aspect_ratio": config.aspect_ratio,
                },
            )

    async def _generate_image(self, config: GenerationConfig) -> GenerationResult:
        """Genera imagen con Runway (Gen-4 image)."""
        import aiohttp

        headers = {
            "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": config.prompt,
            "model": "gen-4-image",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.dev.runwayml.com/v1/image-to-image",  # o endpoint correcto
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    return GenerationResult(
                        success=False,
                        error_message=f"Runway image error {resp.status}: {text}",
                    )
                data = await resp.json()
                image_url = data.get("url") or data.get("output", [{}])[0].get("url")

        return GenerationResult(
            success=True,
            url=image_url,
            cost_usd=0.05,
            model_used="gen-4-image",
            quality_tier=config.quality,
            metadata={},
        )
