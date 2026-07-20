"""Fal.ai Aggregator Provider — Unified access to multiple models

Models available via fal.ai:
- bytedance/seedance/seedance-2-pro/text-to-video
- bytedance/seedance/seedance-2-fast/text-to-video
- fal-ai/flux-pro/v1.1
- fal-ai/flux/dev
- fal-ai/flux/schnell
- fal-ai/kling-video/v1/standard/text-to-video
- fal-ai/luma-dream-machine

Pricing varies by model:
- Flux Schnell: ~$0.003/img
- Flux Pro: ~$0.025/img
- Flux Dev: ~$0.015/img
- Seedance Standard: ~$0.10/s
- Seedance Fast: ~$0.081/s
- Kling: ~$0.06/s
- Luma: ~$0.05/s
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType
from ..utils import download_url, compress_image, smart_quality_for_size, get_image_size_kb

settings = get_settings()

# Endpoints y costos
FAL_MODELS = {
    "flux-schnell": {"endpoint": "fal-ai/flux/schnell", "cost_per_image": 0.003, "type": "image"},
    "flux-dev": {"endpoint": "fal-ai/flux/dev", "cost_per_image": 0.015, "type": "image"},
    "flux-pro": {"endpoint": "fal-ai/flux-pro/v1.1", "cost_per_image": 0.025, "type": "image"},
    "seedance-pro": {"endpoint": "fal-ai/seedance/seedance-2-pro/text-to-video", "cost_per_second": 0.10, "type": "video"},
    "seedance-fast": {"endpoint": "fal-ai/seedance/seedance-2-fast/text-to-video", "cost_per_second": 0.081, "type": "video"},
    "kling": {"endpoint": "fal-ai/kling-video/v1/standard/text-to-video", "cost_per_second": 0.06, "type": "video"},
    "luma": {"endpoint": "fal-ai/luma-dream-machine", "cost_per_second": 0.05, "type": "video"},
}


class FalAggregatorProvider(BaseProvider):
    """Agregador de múltiples modelos via fal.ai."""

    name = "fal.ai"
    slug = "fal_aggregator"
    supports = [ContentType.IMAGE, ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.FAL_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        model_key = config.extra_params.get("fal_model", "flux-pro")
        model_config = FAL_MODELS.get(model_key, FAL_MODELS["flux-pro"])

        if model_config["type"] == "image":
            return model_config["cost_per_image"] * config.num_variations
        else:
            duration = config.duration_seconds or 5
            return model_config["cost_per_second"] * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "flux-schnell": 0.003,
            "flux-dev": 0.015,
            "flux-pro": 0.025,
            "seedance-pro": 0.10,
            "seedance-fast": 0.081,
            "kling": 0.06,
            "luma": 0.05,
        }

    def _select_model(self, config: GenerationConfig) -> str:
        """Selecciona el modelo fal.ai apropiado según config."""
        if config.content_type == ContentType.IMAGE:
            if config.quality == ContentQuality.DRAFT:
                return "flux-schnell"
            elif config.quality == ContentQuality.PREMIUM:
                return "flux-pro"
            return "flux-dev"
        else:  # video
            if config.quality == ContentQuality.DRAFT:
                return "seedance-fast"
            elif config.extra_params.get("model") == "kling":
                return "kling"
            elif config.extra_params.get("model") == "luma":
                return "luma"
            return "seedance-pro"

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="FAL_KEY no configurada")

        try:
            import fal_client
            fal_client.api_key = settings.FAL_KEY

            model_key = self._select_model(config)
            model_config = FAL_MODELS[model_key]
            endpoint = model_config["endpoint"]

            arguments = {"prompt": config.prompt}

            if model_config["type"] == "image":
                arguments["image_size"] = config.extra_params.get("image_size", "square_hd")
                if config.num_variations > 1:
                    arguments["num_images"] = config.num_variations
            else:  # video
                arguments["duration"] = str(min(config.duration_seconds or 5, 10))
                if config.aspect_ratio:
                    arguments["aspect_ratio"] = config.aspect_ratio
                if config.reference_image_url:
                    arguments["image_url"] = config.reference_image_url
                if config.extra_params.get("generate_audio"):
                    arguments["generate_audio"] = True

            result = await fal_client.subscribe_async(endpoint, arguments=arguments)

            # Extraer URL
            url = None
            if hasattr(result, "images") and result.images:
                url = result.images[0].url
            elif hasattr(result, "video") and result.video:
                url = result.video.url
            elif isinstance(result, dict):
                if "images" in result and result["images"]:
                    url = result["images"][0].get("url")
                elif "video" in result:
                    url = result["video"].get("url") if isinstance(result["video"], dict) else result["video"]

            if not url:
                return GenerationResult(success=False, error_message=f"fal.ai ({model_key}) no devolvió resultado")

            # Descargar y comprimir si es imagen
            local = None
            width = height = None
            if model_config["type"] == "image":
                image_bytes = await download_url(url)
                if image_bytes:
                    local = compress_image(image_bytes, quality=smart_quality_for_size(get_image_size_kb(image_bytes)))
                    from PIL import Image as PILImage
                    import io
                    img = PILImage.open(io.BytesIO(local))
                    width, height = img.size

            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                url=url,
                local_path=local,
                cost_usd=cost,
                model_used=f"fal-{model_key}",
                quality_tier=config.quality,
                width=width,
                height=height,
                duration_seconds=config.duration_seconds if model_config["type"] == "video" else None,
                metadata={"fal_model": model_key, "endpoint": endpoint},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
