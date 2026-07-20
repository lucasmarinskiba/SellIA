"""Replicate Provider — Stable Diffusion 3.5, Flux, y más.

Pricing aproximado (2026):
- Stable Diffusion 3.5: ~$0.008-0.015/imagen
- Flux Schnell: ~$0.015/imagen
- Flux Dev: ~$0.025/imagen
- Flux Pro: ~$0.055/imagen

Este es nuestro proveedor de bajo costo para drafts y alta volumetría.
"""

import asyncio
import io
from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import compress_image, smart_quality_for_size, get_image_size_kb, download_url

settings = get_settings()

# Modelos Replicate por calidad
REPLICATE_MODELS = {
    ContentQuality.DRAFT: {
        "model": "black-forest-labs/flux-schnell",
        "cost_per_image": 0.015,
        "version": None,  # Usar latest
    },
    ContentQuality.STANDARD: {
        "model": "black-forest-labs/flux-dev",
        "cost_per_image": 0.025,
        "version": None,
    },
    ContentQuality.PREMIUM: {
        "model": "black-forest-labs/flux-pro",
        "cost_per_image": 0.055,
        "version": None,
    },
}

# Alternativa con Stable Diffusion para máximo ahorro
SD_FALLBACK = {
    "model": "stability-ai/stable-diffusion-3.5-large",
    "cost_per_image": 0.012,
}


class ReplicateProvider(BaseProvider):
    """Proveedor de imágenes/videos usando Replicate API."""

    name = "Replicate"
    slug = "replicate"
    supports = [ContentType.IMAGE, ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.REPLICATE_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        if config.content_type == ContentType.IMAGE:
            model_config = REPLICATE_MODELS.get(config.quality, REPLICATE_MODELS[ContentQuality.STANDARD])
            return model_config["cost_per_image"] * config.num_variations
        elif config.content_type == ContentType.VIDEO:
            # Video en Replicate: ~$0.03-0.05/segundo
            duration = config.duration_seconds or 5
            return 0.04 * duration * config.num_variations
        return 0.0

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "flux-schnell": 0.015,
            "flux-dev": 0.025,
            "flux-pro": 0.055,
            "sd-3.5-large": 0.012,
            "video-standard": 0.04,  # per second
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="REPLICATE_API_KEY no configurada",
            )

        try:
            import replicate

            client = replicate.Client(api_token=settings.REPLICATE_API_KEY)

            if config.content_type == ContentType.IMAGE:
                return await self._generate_image(client, config)
            elif config.content_type == ContentType.VIDEO:
                return await self._generate_video(client, config)
            else:
                return GenerationResult(
                    success=False,
                    error_message=f"Tipo {config.content_type.value} no soportado por Replicate",
                )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )

    async def _generate_image(self, client, config: GenerationConfig) -> GenerationResult:
        model_config = REPLICATE_MODELS.get(config.quality, REPLICATE_MODELS[ContentQuality.STANDARD])

        input_params = {
            "prompt": config.prompt,
            "num_outputs": config.num_variations,
        }

        if config.negative_prompt:
            input_params["negative_prompt"] = config.negative_prompt

        if config.width and config.height:
            input_params["width"] = config.width
            input_params["height"] = config.height
        elif config.aspect_ratio:
            # Mapear aspect ratio a dimensiones
            ar_map = {
                "1:1": (1024, 1024),
                "16:9": (1024, 576),
                "9:16": (576, 1024),
                "4:3": (1024, 768),
                "3:4": (768, 1024),
            }
            w, h = ar_map.get(config.aspect_ratio, (1024, 1024))
            input_params["width"] = w
            input_params["height"] = h

        if config.seed is not None:
            input_params["seed"] = config.seed

        # Ejecutar predicción
        output = await asyncio.to_thread(
            client.run,
            model_config["model"],
            input=input_params,
        )

        # Replicate devuelve lista de URLs
        urls = output if isinstance(output, list) else [output]
        if not urls:
            return GenerationResult(success=False, error_message="Replicate devolvió resultado vacío")

        # Descargar y comprimir primera imagen
        image_bytes = await download_url(urls[0])
        compressed = None
        width = height = None

        if image_bytes:
            compressed = compress_image(
                image_bytes,
                target_format="JPEG",
                quality=smart_quality_for_size(get_image_size_kb(image_bytes)),
                max_dimension=2048,
            )
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(compressed))
            width, height = img.size

        return GenerationResult(
            success=True,
            url=urls[0],
            local_path=compressed,
            cost_usd=model_config["cost_per_image"] * config.num_variations,
            model_used=model_config["model"],
            quality_tier=config.quality,
            width=width,
            height=height,
            metadata={
                "all_urls": urls,
                "input_params": input_params,
            },
        )

    async def _generate_video(self, client, config: GenerationConfig) -> GenerationResult:
        """Genera video usando modelos de video en Replicate."""
        # Modelo de video recomendado en Replicate
        video_models = {
            ContentQuality.DRAFT: "luma-ai/dream-machine",
            ContentQuality.STANDARD: "kwaivgi/kling",
            ContentQuality.PREMIUM: "minimax/video-01",
        }

        model = video_models.get(config.quality, video_models[ContentQuality.STANDARD])
        duration = config.duration_seconds or 5

        input_params = {
            "prompt": config.prompt,
        }

        if config.reference_image_url:
            input_params["image"] = config.reference_image_url

        output = await asyncio.to_thread(
            client.run,
            model,
            input=input_params,
        )

        urls = output if isinstance(output, list) else [output]
        if not urls:
            return GenerationResult(success=False, error_message="Replicate devolvió video vacío")

        cost = 0.04 * duration  # aproximado

        return GenerationResult(
            success=True,
            url=urls[0],
            cost_usd=cost,
            model_used=model,
            quality_tier=config.quality,
            duration_seconds=duration,
            metadata={"all_urls": urls},
        )
