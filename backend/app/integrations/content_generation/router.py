"""Smart Content Generation Router"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .base import (
    BaseProvider, GenerationConfig, GenerationResult,
    ContentQuality, ContentType,
)
from .cache import ContentCache
from .budget import BudgetController
from .plan_tools import (
    get_tools_for_plan, is_tool_allowed, get_fallback_tool,
    get_plan_upgrade_message, TOOL_REGISTRY,
)
from .providers import (
    OpenAIImageProvider,
    ReplicateProvider,
    RunwayProvider,
    SeedanceProvider,
    ElevenLabsProvider,
    LeonardoProvider,
    PhotoroomProvider,
    IdeogramProvider,
    MidjourneyProvider,
    HeyGenProvider,
    PikaProvider,
    OpusClipProvider,
    CopyAIProvider,
    JasperProvider,
    BeautifulAIProvider,
    GammaProvider,
    KlingProvider,
    LumaProvider,
    AdCreativeProvider,
    WritesonicProvider,
    CanvaProvider,
    CapCutProvider,
    SoraProvider,
    FalAggregatorProvider,
    KimiProvider,
    OllamaProvider,
)


@dataclass
class RoutingDecision:
    """Decisión de routing con justificación."""
    provider: BaseProvider
    quality: ContentQuality
    estimated_cost: float
    reason: str
    cached: bool = False
    cached_result: Optional[dict] = None


class ContentGenerationRouter:
    """Router inteligente para generación de contenido."""

    def __init__(self):
        self.cache = ContentCache()
        self.budget = BudgetController()
        self.providers = self._init_providers()

    def _init_providers(self) -> Dict[str, BaseProvider]:
        """Inicializa todos los proveedores disponibles."""
        return {
            "openai_image": OpenAIImageProvider(),
            "replicate": ReplicateProvider(),
            "runway": RunwayProvider(),
            "seedance": SeedanceProvider(),
            "elevenlabs": ElevenLabsProvider(),
            "leonardo": LeonardoProvider(),
            "photoroom": PhotoroomProvider(),
            "ideogram": IdeogramProvider(),
            "midjourney": MidjourneyProvider(),
            "heygen": HeyGenProvider(),
            "pika": PikaProvider(),
            "opusclip": OpusClipProvider(),
            "copyai": CopyAIProvider(),
            "jasper": JasperProvider(),
            "beautifulai": BeautifulAIProvider(),
            "gamma": GammaProvider(),
            "kling": KlingProvider(),
            "luma": LumaProvider(),
            "adcreative": AdCreativeProvider(),
            "writesonic": WritesonicProvider(),
            "canva": CanvaProvider(),
            "capcut": CapCutProvider(),
            "sora": SoraProvider(),
            "fal_aggregator": FalAggregatorProvider(),
            "kimi": KimiProvider(),
            "ollama": OllamaProvider(),
        }

    def _get_available_providers(
        self,
        content_type: ContentType,
    ) -> List[BaseProvider]:
        """Filtra proveedores disponibles por tipo de contenido."""
        available = []
        for provider in self.providers.values():
            if provider.is_available and content_type in provider.supports:
                available.append(provider)
        return available

    def _select_provider_for_quality(
        self,
        content_type: ContentType,
        quality: ContentQuality,
        available: List[BaseProvider],
    ) -> Optional[BaseProvider]:
        """Selecciona proveedor preferido según tipo y calidad."""

        # Routing matrix
        routing = {
            (ContentType.IMAGE, ContentQuality.DRAFT): ["replicate", "openai_image"],
            (ContentType.IMAGE, ContentQuality.STANDARD): ["openai_image", "replicate"],
            (ContentType.IMAGE, ContentQuality.PREMIUM): ["openai_image", "replicate"],
            (ContentType.VIDEO, ContentQuality.DRAFT): ["runway", "replicate", "seedance"],
            (ContentType.VIDEO, ContentQuality.STANDARD): ["runway", "seedance", "replicate"],
            (ContentType.VIDEO, ContentQuality.PREMIUM): ["seedance", "runway", "replicate"],
            (ContentType.AUDIO, ContentQuality.DRAFT): ["elevenlabs"],
            (ContentType.AUDIO, ContentQuality.STANDARD): ["elevenlabs"],
            (ContentType.AUDIO, ContentQuality.PREMIUM): ["elevenlabs"],
        }

        preferred_slugs = routing.get((content_type, quality), [])
        slug_map = {p.slug: p for p in available}

        for slug in preferred_slugs:
            if slug in slug_map:
                return slug_map[slug]

        # Fallback: cualquier disponible
        return available[0] if available else None

    async def route(
        self,
        business_id: str,
        config: GenerationConfig,
        plan_tier: str = "starter",
    ) -> RoutingDecision:
        """
        Decide qué proveedor y calidad usar.

        Returns:
            RoutingDecision con proveedor seleccionado, calidad ajustada,
            costo estimado y justificación.
        """
        content_type = config.content_type
        requested_quality = config.quality
        requested_tool = config.extra_params.get("tool")

        # 0. Verificar si la herramienta solicitada está permitida por plan
        if requested_tool and not is_tool_allowed(requested_tool, plan_tier):
            upgrade_msg = get_plan_upgrade_message(requested_tool, plan_tier)
            # Intentar fallback a herramienta permitida
            fallback = get_fallback_tool(requested_tool, plan_tier)
            if fallback:
                config.extra_params["tool"] = fallback
                requested_tool = fallback
            else:
                return RoutingDecision(
                    provider=None,  # type: ignore
                    quality=requested_quality,
                    estimated_cost=0.0,
                    reason=f"{upgrade_msg}. Modo prompt-only.",
                )

        # 1. Check cache de resultados
        cache_key = {
            "prompt": config.prompt,
            "content_type": content_type.value,
            "quality": requested_quality.value,
            "width": config.width,
            "height": config.height,
            "aspect_ratio": config.aspect_ratio,
            "duration": config.duration_seconds,
            "style": config.style,
        }

        # Buscar en caché por hash de config
        available_providers = self._get_available_providers(content_type)
        for provider in available_providers:
            cached = await self.cache.get_cached_result(provider.slug, cache_key)
            if cached:
                return RoutingDecision(
                    provider=provider,
                    quality=requested_quality,
                    estimated_cost=0.0,
                    reason="Resultado cacheado (sin costo)",
                    cached=True,
                    cached_result=cached,
                )

        # 2. Filtrar proveedores por herramientas permitidas del plan
        allowed_tools = set(get_tools_for_plan(plan_tier))
        allowed_providers = []
        for p in available_providers:
            # Mapear provider slug a tool slugs
            provider_tools = [t for t, info in TOOL_REGISTRY.items() if info.provider_module == p.slug]
            if any(t in allowed_tools for t in provider_tools):
                allowed_providers.append(p)

        if not allowed_providers:
            return RoutingDecision(
                provider=None,  # type: ignore
                quality=requested_quality,
                estimated_cost=0.0,
                reason=f"Tu plan {plan_tier.upper()} no incluye herramientas de {content_type.value}. Modo prompt-only.",
            )

        # 3. Seleccionar proveedor preferido (de los permitidos)
        provider = self._select_provider_for_quality(content_type, requested_quality, allowed_providers)
        if not provider:
            return RoutingDecision(
                provider=None,  # type: ignore
                quality=requested_quality,
                estimated_cost=0.0,
                reason="Ningún proveedor permitido soporta este tipo de contenido",
            )

        estimated_cost = provider.estimate_cost(config)

        # 4. Check budget
        allowed, reason = await self.budget.check_budget(
            business_id, content_type, estimated_cost, plan_tier
        )

        if not allowed:
            # Intentar fallback a calidad más barata
            policy = self.budget.get_policy(plan_tier)
            fallback_quality = self.budget.select_quality_fallback(requested_quality, policy)

            if fallback_quality != requested_quality:
                config.quality = fallback_quality
                provider = self._select_provider_for_quality(content_type, fallback_quality, allowed_providers)
                if provider:
                    estimated_cost = provider.estimate_cost(config)
                    allowed, _ = await self.budget.check_budget(
                        business_id, content_type, estimated_cost, plan_tier
                    )
                    if allowed:
                        return RoutingDecision(
                            provider=provider,
                            quality=fallback_quality,
                            estimated_cost=estimated_cost,
                            reason=f"Calidad reducida de {requested_quality.value} a {fallback_quality.value} por presupuesto: {reason}",
                        )

            # Último fallback: prompt-only
            return RoutingDecision(
                provider=None,  # type: ignore
                quality=requested_quality,
                estimated_cost=0.0,
                reason=f"Presupuesto excedido: {reason}. Modo prompt-only.",
            )

        return RoutingDecision(
            provider=provider,
            quality=requested_quality,
            estimated_cost=estimated_cost,
            reason=f"Proveedor: {provider.name}, calidad: {requested_quality.value}",
        )

    async def generate(
        self,
        business_id: str,
        config: GenerationConfig,
        plan_tier: str = "starter",
    ) -> GenerationResult:
        """
        Genera contenido usando el router inteligente.

        Este es el método principal que usa content_tasks.py.
        """
        decision = await self.route(business_id, config, plan_tier)

        # Si está cacheado, devolver directamente
        if decision.cached and decision.cached_result:
            result_data = decision.cached_result
            return GenerationResult(
                success=True,
                url=result_data.get("url"),
                text_content=result_data.get("text_content"),
                cost_usd=0.0,
                model_used=result_data.get("model_used", "cached"),
                quality_tier=decision.quality,
                metadata={"cached": True, **result_data.get("metadata", {})},
            )

        # Si no hay proveedor (prompt-only)
        if decision.provider is None:
            return GenerationResult(
                success=True,
                text_content=config.prompt,
                cost_usd=0.0,
                model_used="prompt-only",
                quality_tier=decision.quality,
                metadata={
                    "mode": "prompt-only",
                    "reason": decision.reason,
                    "prompt": config.prompt,
                },
            )

        # Generar con proveedor seleccionado
        result = await decision.provider.generate(config)

        # Registrar gasto
        if result.success and result.cost_usd > 0:
            await self.budget.record_spend(
                business_id, config.content_type, result.cost_usd, decision.provider.slug
            )

        # Cachear resultado
        if result.success:
            cache_key = {
                "prompt": config.prompt,
                "content_type": config.content_type.value,
                "quality": config.quality.value,
                "width": config.width,
                "height": config.height,
                "aspect_ratio": config.aspect_ratio,
                "duration": config.duration_seconds,
                "style": config.style,
            }
            cache_data = {
                "url": result.url,
                "text_content": result.text_content,
                "model_used": result.model_used,
                "metadata": result.metadata,
            }
            await self.cache.cache_result(
                decision.provider.slug, cache_key, cache_data, config.quality.value
            )

        return result

    def get_pricing_summary(self, plan_tier: str = "starter") -> Dict[str, Dict]:
        """Retorna resumen de precios de herramientas disponibles para el plan."""
        from .plan_tools import get_tools_for_plan, TOOL_REGISTRY
        allowed = set(get_tools_for_plan(plan_tier))
        summary = {}
        for tool_slug in allowed:
            tool = TOOL_REGISTRY.get(tool_slug)
            if not tool:
                continue
            provider = self.providers.get(tool.provider_module)
            if provider and provider.is_available:
                summary[tool_slug] = {
                    "name": tool.name,
                    "category": tool.category,
                    "pricing": provider.get_pricing_table(),
                }
            else:
                summary[tool_slug] = {
                    "name": tool.name,
                    "category": tool.category,
                    "pricing": {"prompt-only": 0.0},
                    "note": "API key no configurada",
                }
        return summary
