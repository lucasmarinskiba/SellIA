"""Budget control for content generation.

Controla el gasto diario por negocio y proveedor.
Implementa políticas de fallback (si se excede el presupuesto,
se cambia a tier más barato o a modo prompt-only).
"""

from typing import Optional, Dict
from dataclasses import dataclass
from .base import ContentQuality, ContentType
from .cache import ContentCache


@dataclass
class BudgetPolicy:
    """Política de presupuesto para un negocio."""
    daily_budget_usd: float = 5.0
    daily_image_budget_usd: float = 3.0
    daily_video_budget_usd: float = 2.0
    daily_copy_budget_usd: float = 0.5
    max_images_per_day: int = 20
    max_videos_per_day: int = 5
    max_copies_per_day: int = 50
    max_presentations_per_day: int = 5
    fallback_on_exceed: bool = True
    prompt_only_fallback: bool = True
    # Content generation limits by plan
    max_video_duration_seconds: int = 15
    max_image_resolution: str = "1792x1024"
    supports_4k: bool = False
    supports_custom_models: bool = False


# Políticas por plan de suscripción
DEFAULT_POLICIES = {
    "free": BudgetPolicy(
        daily_budget_usd=1.0,
        daily_image_budget_usd=0.5,
        daily_video_budget_usd=0.5,
        daily_copy_budget_usd=0.1,
        max_images_per_day=5,
        max_videos_per_day=1,
        max_copies_per_day=10,
        max_presentations_per_day=1,
        fallback_on_exceed=True,
        prompt_only_fallback=True,
        max_video_duration_seconds=5,
        max_image_resolution="1024x1024",
        supports_4k=False,
        supports_custom_models=False,
    ),
    "starter": BudgetPolicy(
        daily_budget_usd=5.0,
        daily_image_budget_usd=3.0,
        daily_video_budget_usd=2.0,
        daily_copy_budget_usd=0.5,
        max_images_per_day=20,
        max_videos_per_day=5,
        max_copies_per_day=50,
        max_presentations_per_day=5,
        fallback_on_exceed=True,
        prompt_only_fallback=False,
        max_video_duration_seconds=15,
        max_image_resolution="1792x1024",
        supports_4k=False,
        supports_custom_models=False,
    ),
    "pro": BudgetPolicy(
        daily_budget_usd=20.0,
        daily_image_budget_usd=12.0,
        daily_video_budget_usd=8.0,
        daily_copy_budget_usd=1.0,
        max_images_per_day=100,
        max_videos_per_day=20,
        max_copies_per_day=200,
        max_presentations_per_day=20,
        fallback_on_exceed=True,
        prompt_only_fallback=False,
        max_video_duration_seconds=30,
        max_image_resolution="2048x2048",
        supports_4k=True,
        supports_custom_models=False,
    ),
    "enterprise": BudgetPolicy(
        daily_budget_usd=100.0,
        daily_image_budget_usd=60.0,
        daily_video_budget_usd=40.0,
        daily_copy_budget_usd=5.0,
        max_images_per_day=500,
        max_videos_per_day=100,
        max_copies_per_day=1000,
        max_presentations_per_day=100,
        fallback_on_exceed=False,
        prompt_only_fallback=False,
        max_video_duration_seconds=60,
        max_image_resolution="4K",
        supports_4k=True,
        supports_custom_models=True,
    ),
}


class BudgetController:
    """Controla presupuestos y aplica políticas de fallback."""

    def __init__(self):
        self.cache = ContentCache()

    def get_policy(self, plan_tier: str) -> BudgetPolicy:
        """Obtiene política según tier de suscripción."""
        return DEFAULT_POLICIES.get(plan_tier, DEFAULT_POLICIES["starter"])

    async def check_budget(
        self,
        business_id: str,
        content_type: ContentType,
        estimated_cost: float,
        plan_tier: str = "starter",
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica si hay presupuesto disponible.

        Returns:
            (allowed, reason): allowed=True si se puede generar,
            reason=None si está OK, o string explicando por qué no.
        """
        policy = self.get_policy(plan_tier)
        cache = self.cache

        # Check total daily budget
        total_spend = await cache.get_daily_spend(business_id, "total")
        if total_spend + estimated_cost > policy.daily_budget_usd:
            return False, f"Presupuesto diario excedido: ${total_spend:.2f}/${policy.daily_budget_usd:.2f}"

        # Check type-specific budget
        type_budget_map = {
            ContentType.IMAGE: (policy.daily_image_budget_usd, policy.max_images_per_day),
            ContentType.VIDEO: (policy.daily_video_budget_usd, policy.max_videos_per_day),
            ContentType.AUDIO: (policy.daily_video_budget_usd, policy.max_videos_per_day),
            ContentType.COPY: (policy.daily_copy_budget_usd, policy.max_copies_per_day),
        }

        type_budget, type_max = type_budget_map.get(content_type, (policy.daily_budget_usd, 9999))
        type_spend = await cache.get_daily_spend(business_id, content_type.value)
        type_count = await cache.get_daily_generations(business_id, content_type.value)

        if type_spend + estimated_cost > type_budget:
            return False, f"Presupuesto de {content_type.value} excedido: ${type_spend:.2f}/${type_budget:.2f}"

        if type_count + 1 > type_max:
            return False, f"Límite diario de {content_type.value} alcanzado: {type_count}/{type_max}"

        return True, None

    async def record_spend(
        self,
        business_id: str,
        content_type: ContentType,
        cost: float,
        provider: str,
    ):
        """Registra gasto en caché."""
        await self.cache.increment_spend(business_id, "total", cost)
        await self.cache.increment_spend(business_id, content_type.value, cost)
        await self.cache.increment_spend(business_id, provider, cost)
        await self.cache.increment_generation(business_id, content_type.value)

    def select_quality_fallback(
        self,
        requested: ContentQuality,
        policy: BudgetPolicy,
    ) -> ContentQuality:
        """Selecciona calidad fallback si el presupuesto es limitado."""
        if not policy.fallback_on_exceed:
            return requested

        fallback_map = {
            ContentQuality.PREMIUM: ContentQuality.STANDARD,
            ContentQuality.STANDARD: ContentQuality.DRAFT,
            ContentQuality.DRAFT: ContentQuality.DRAFT,
        }
        return fallback_map.get(requested, ContentQuality.DRAFT)

    def should_use_prompt_only(
        self,
        plan_tier: str,
        total_spend: float,
        estimated_cost: float,
    ) -> bool:
        """Determina si debe usarse modo prompt-only para ahorrar."""
        policy = self.get_policy(plan_tier)
        if not policy.prompt_only_fallback:
            return False
        if total_spend + estimated_cost > policy.daily_budget_usd * 0.9:
            return True
        return False

    async def get_usage_report(self, business_id: str) -> Dict:
        """Genera reporte de uso del día."""
        cache = self.cache
        return {
            "total_spend": await cache.get_daily_spend(business_id, "total"),
            "image_spend": await cache.get_daily_spend(business_id, ContentType.IMAGE.value),
            "video_spend": await cache.get_daily_spend(business_id, ContentType.VIDEO.value),
            "copy_spend": await cache.get_daily_spend(business_id, ContentType.COPY.value),
            "image_count": await cache.get_daily_generations(business_id, ContentType.IMAGE.value),
            "video_count": await cache.get_daily_generations(business_id, ContentType.VIDEO.value),
            "copy_count": await cache.get_daily_generations(business_id, ContentType.COPY.value),
        }
