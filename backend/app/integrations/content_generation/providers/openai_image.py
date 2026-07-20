"""OpenAI Image Provider — DALL-E 3 / GPT Image 1

Pricing (2026):
- DALL-E 3 Standard 1024x1024: $0.04
- DALL-E 3 HD 1024x1024: $0.08
- GPT Image 1 Mini Low: $0.005
- GPT Image 1 Mini High: $0.036
- GPT Image 1 Low: $0.011
- GPT Image 1 High: $0.167

Usamos GPT Image 1 Mini para drafts (muy barato),
DALL-E 3 Standard para standard,
y DALL-E 3 HD o GPT Image 1 High para premium.
"""

import asyncio
from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()

# Model mapping por calidad
QUALITY_MODELS = {
    ContentQuality.DRAFT: {
        "model": "gpt-image-1-mini",
        "quality": "low",
        "cost_per_image": 0.005,
    },
    ContentQuality.STANDARD: {
        "model": "dall-e-3",
        "quality": "standard",
        "cost_per_image": 0.04,
        "size": "1024x1024",
    },
    ContentQuality.PREMIUM: {
        "model": "dall-e-3",
        "quality": "hd",
        "cost_per_image": 0.08,
        "size": "1024x1024",
    },
}

# Fallback: si HD no está disponible, usar standard
PREMIUM_FALLBACK = {
    "model": "gpt-image-1",
    "quality": "high",
    "cost_per_image": 0.167,
}


class OpenAIImageProvider(BaseProvider):
    """Proveedor de imágenes usando OpenAI API."""

    name = "OpenAI Image"
    slug = "openai_image"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        model_config = QUALITY_MODELS.get(config.quality, QUALITY_MODELS[ContentQuality.STANDARD])
        return model_config["cost_per_image"] * config.num_variations

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "gpt-image-1-mini-low": 0.005,
            "gpt-image-1-mini-high": 0.036,
            "gpt-image-1-low": 0.011,
            "gpt-image-1-medium": 0.042,
            "gpt-image-1-high": 0.167,
            "dall-e-3-standard": 0.04,
            "dall-e-3-hd": 0.08,
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="OPENAI_API_KEY no configurada",
            )

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            model_config = QUALITY_MODELS.get(
                config.quality,
                QUALITY_MODELS[ContentQuality.STANDARD]
            )

            # Para variaciones, generamos en paralelo
            tasks = []
            for _ in range(config.num_variations):
                task = self._generate_single(
                    client=client,
                    prompt=config.prompt,
                    model_config=model_config,
                    negative_prompt=config.negative_prompt,
                    size=config.extra_params.get("size", model_config.get("size", "1024x1024")),
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Tomamos el primer resultado exitoso
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result.success:
                    return result

            # Si ninguno tuvo éxito, devolvemos el primer error
            for result in results:
                if isinstance(result, Exception):
                    return GenerationResult(
                        success=False,
                        error_message=f"Error en generación: {result}",
                    )

            return GenerationResult(
                success=False,
                error_message="Todas las variaciones fallaron",
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )

    async def _generate_single(
        self,
        client,
        prompt: str,
        model_config: Dict[str, Any],
        negative_prompt: Optional[str] = None,
        size: str = "1024x1024",
    ) -> GenerationResult:
        """Genera una sola imagen."""
        try:
            # DALL-E 3 no soporta negative_prompt nativamente,
            # lo incorporamos al prompt si existe
            full_prompt = prompt
            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"

            response = await client.images.generate(
                model=model_config["model"],
                prompt=full_prompt,
                size=size,
                quality=model_config["quality"],
                n=1,
                response_format="url",
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt or prompt

            # Intentamos descargar y comprimir
            from ..utils import download_url, compress_image, get_image_dimensions
            image_bytes = await download_url(image_url)

            if image_bytes:
                # Comprimir para ahorrar storage
                compressed = compress_image(
                    image_bytes,
                    target_format="JPEG",
                    quality=smart_quality_for_size(get_image_size_kb(image_bytes)),
                    max_dimension=2048,
                )
                width, height = get_image_dimensions(compressed)
            else:
                compressed = None
                width, height = None, None

            return GenerationResult(
                success=True,
                url=image_url,
                local_path=compressed,
                cost_usd=model_config["cost_per_image"],
                model_used=model_config["model"],
                quality_tier=ContentQuality.STANDARD if model_config["quality"] == "standard" else ContentQuality.PREMIUM if model_config["quality"] == "hd" else ContentQuality.DRAFT,
                width=width,
                height=height,
                metadata={
                    "revised_prompt": revised_prompt,
                    "size": size,
                    "compressed_size_kb": len(compressed) / 1024 if compressed else None,
                },
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )
