"""Plan Tools — Fuente de verdad para herramientas de IA por plan de suscripción.

Mapea cada herramienta al plan mínimo requerido, su categoría,
costo estimado, y metadatos para el router y la UI.
"""

from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class ToolInfo:
    """Metadatos de una herramienta de IA generativa."""
    slug: str
    name: str
    category: str  # image, video, audio, copy, design, presentation
    min_plan: str  # free, starter, pro, enterprise
    cost_tier: str  # ultra_low, low, medium, high, premium
    description: str
    provider_module: str  # nombre del archivo provider
    requires_api_key: bool = True
    fallback_tool: str = ""  # herramienta alternativa si no está disponible
    supports_batch: bool = False


# ============================================================================
# REGISTRO DE HERRAMIENTAS (26 herramientas)
# ============================================================================

TOOL_REGISTRY: Dict[str, ToolInfo] = {
    # === FREE TIER (9 herramientas) ===
    "chatgpt": ToolInfo(
        slug="chatgpt",
        name="ChatGPT / GPT-4o-mini",
        category="copy",
        min_plan="free",
        cost_tier="ultra_low",
        description="Copy, captions, descripciones de producto. El más económico.",
        provider_module="openai_image",  # Reusa OpenAI client
        requires_api_key=True,
        fallback_tool="",
    ),
    "canva": ToolInfo(
        slug="canva",
        name="Canva AI",
        category="design",
        min_plan="free",
        cost_tier="ultra_low",
        description="Diseño gráfico, posts, stories, banners con templates.",
        provider_module="canva",
        requires_api_key=True,
        fallback_tool="",
    ),
    "capcut": ToolInfo(
        slug="capcut",
        name="CapCut AI",
        category="video",
        min_plan="free",
        cost_tier="ultra_low",
        description="Edición de video, auto-captions, efectos, templates virales.",
        provider_module="capcut",
        requires_api_key=True,
        fallback_tool="",
    ),
    "ideogram": ToolInfo(
        slug="ideogram",
        name="Ideogram 2.0",
        category="image",
        min_plan="free",
        cost_tier="low",
        description="Imágenes con texto preciso. Logos, posters, infografías.",
        provider_module="ideogram",
        requires_api_key=True,
        fallback_tool="",
    ),
    "replicate_flux_schnell": ToolInfo(
        slug="replicate_flux_schnell",
        name="Flux Schnell (Replicate)",
        category="image",
        min_plan="free",
        cost_tier="ultra_low",
        description="Imágenes ultra-rápidas y baratas para drafts.",
        provider_module="replicate",
        requires_api_key=True,
        fallback_tool="",
    ),
    "fal_flux_pro": ToolInfo(
        slug="fal_flux_pro",
        name="Flux Pro (fal.ai)",
        category="image",
        min_plan="free",
        cost_tier="low",
        description="Imágenes de alta calidad para productos.",
        provider_module="fal_aggregator",
        requires_api_key=True,
        fallback_tool="replicate_flux_schnell",
    ),
    "gpt_image_mini": ToolInfo(
        slug="gpt_image_mini",
        name="GPT Image 1 Mini",
        category="image",
        min_plan="free",
        cost_tier="ultra_low",
        description="Imágenes básicas generadas por ChatGPT.",
        provider_module="openai_image",
        requires_api_key=True,
        fallback_tool="",
    ),
    "kimi": ToolInfo(
        slug="kimi",
        name="Kimi (Moonshot AI)",
        category="copy",
        min_plan="free",
        cost_tier="ultra_low",
        description="Copy, captions, emails, scripts. 256K contexto, ultra-barato, excelente en español.",
        provider_module="kimi",
        requires_api_key=True,
        fallback_tool="ollama",
    ),
    "ollama": ToolInfo(
        slug="ollama",
        name="Ollama (Local LLM)",
        category="copy",
        min_plan="free",
        cost_tier="ultra_low",
        description="Copy gratuito usando modelos locales (Llama, Mistral, Qwen). Requiere Ollama instalado.",
        provider_module="ollama",
        requires_api_key=False,
        fallback_tool="kimi",
    ),

    # === STARTER TIER (+6 herramientas = 15 total) ===
    "dalle3": ToolInfo(
        slug="dalle3",
        name="DALL-E 3",
        category="image",
        min_plan="starter",
        cost_tier="medium",
        description="Imágenes premium con excelente calidad y prompt following.",
        provider_module="openai_image",
        requires_api_key=True,
        fallback_tool="fal_flux_pro",
    ),
    "leonardo": ToolInfo(
        slug="leonardo",
        name="Leonardo.ai",
        category="image",
        min_plan="starter",
        cost_tier="low",
        description="Imágenes artísticas, concept art, game assets, Alchemy.",
        provider_module="leonardo",
        requires_api_key=True,
        fallback_tool="dalle3",
    ),
    "photoroom": ToolInfo(
        slug="photoroom",
        name="Photoroom",
        category="image",
        min_plan="starter",
        cost_tier="low",
        description="Fotos de producto, background removal, batch editing.",
        provider_module="photoroom",
        requires_api_key=True,
        fallback_tool="dalle3",
    ),
    "opusclip": ToolInfo(
        slug="opusclip",
        name="Opus Clip",
        category="video",
        min_plan="starter",
        cost_tier="low",
        description="Convierte videos largos en Reels/TikToks virales.",
        provider_module="opusclip",
        requires_api_key=True,
        fallback_tool="capcut",
    ),
    "copyai": ToolInfo(
        slug="copyai",
        name="Copy.ai",
        category="copy",
        min_plan="starter",
        cost_tier="ultra_low",
        description="Copy de marketing rápido: ads, headlines, social.",
        provider_module="copyai",
        requires_api_key=True,
        fallback_tool="chatgpt",
    ),
    "jasper": ToolInfo(
        slug="jasper",
        name="Jasper",
        category="copy",
        min_plan="starter",
        cost_tier="low",
        description="Copy largo: emails, sequences, blog posts, brand voice.",
        provider_module="jasper",
        requires_api_key=True,
        fallback_tool="chatgpt",
    ),
    "beautifulai": ToolInfo(
        slug="beautifulai",
        name="Beautiful.ai",
        category="presentation",
        min_plan="starter",
        cost_tier="low",
        description="Presentaciones automáticas con diseño inteligente.",
        provider_module="beautifulai",
        requires_api_key=True,
        fallback_tool="",
    ),

    # === PRO TIER (+6 herramientas = 21 total) ===
    "midjourney": ToolInfo(
        slug="midjourney",
        name="Midjourney",
        category="image",
        min_plan="pro",
        cost_tier="medium",
        description="Imágenes artísticas de la más alta calidad estética.",
        provider_module="midjourney",
        requires_api_key=True,
        fallback_tool="leonardo",
    ),
    "runway": ToolInfo(
        slug="runway",
        name="Runway Gen-4",
        category="video",
        min_plan="pro",
        cost_tier="high",
        description="Video AI con control de movimiento, camera controls, inpainting.",
        provider_module="runway",
        requires_api_key=True,
        fallback_tool="capcut",
    ),
    "heygen": ToolInfo(
        slug="heygen",
        name="HeyGen",
        category="video",
        min_plan="pro",
        cost_tier="premium",
        description="Avatares AI realistas, multilingual videos, lip sync.",
        provider_module="heygen",
        requires_api_key=True,
        fallback_tool="runway",
    ),
    "pika": ToolInfo(
        slug="pika",
        name="Pika Labs",
        category="video",
        min_plan="pro",
        cost_tier="medium",
        description="Video estilizado, anime, efectos especiales.",
        provider_module="pika",
        requires_api_key=True,
        fallback_tool="runway",
    ),
    "elevenlabs": ToolInfo(
        slug="elevenlabs",
        name="ElevenLabs",
        category="audio",
        min_plan="pro",
        cost_tier="medium",
        description="Voiceover de alta calidad, voice cloning, sound effects.",
        provider_module="elevenlabs",
        requires_api_key=True,
        fallback_tool="",
    ),
    "gamma": ToolInfo(
        slug="gamma",
        name="Gamma",
        category="presentation",
        min_plan="pro",
        cost_tier="low",
        description="Docs y presentaciones interactivas con IA.",
        provider_module="gamma",
        requires_api_key=True,
        fallback_tool="beautifulai",
    ),

    # === ENTERPRISE TIER (+7 herramientas = 26 total) ===
    "seedance": ToolInfo(
        slug="seedance",
        name="Seedance 2.0",
        category="video",
        min_plan="enterprise",
        cost_tier="premium",
        description="Video cinematográfico de ByteDance. Calidad de película.",
        provider_module="fal_aggregator",
        requires_api_key=True,
        fallback_tool="runway",
    ),
    "kling": ToolInfo(
        slug="kling",
        name="Kling AI",
        category="video",
        min_plan="enterprise",
        cost_tier="high",
        description="Video con física realista, movimiento humano natural.",
        provider_module="fal_aggregator",
        requires_api_key=True,
        fallback_tool="runway",
    ),
    "sora": ToolInfo(
        slug="sora",
        name="Sora (OpenAI)",
        category="video",
        min_plan="enterprise",
        cost_tier="premium",
        description="Video generativo de OpenAI. Fotorrealismo y narrativa.",
        provider_module="sora",
        requires_api_key=True,
        fallback_tool="seedance",
    ),
    "sd35": ToolInfo(
        slug="sd35",
        name="Stable Diffusion 3.5",
        category="image",
        min_plan="enterprise",
        cost_tier="low",
        description="Imágenes open-source con custom models y fine-tuning.",
        provider_module="replicate",
        requires_api_key=True,
        fallback_tool="midjourney",
    ),
    "adcreative": ToolInfo(
        slug="adcreative",
        name="AdCreative.ai",
        category="design",
        min_plan="enterprise",
        cost_tier="medium",
        description="Creativos de ads optimizados para Meta, Google, TikTok.",
        provider_module="adcreative",
        requires_api_key=True,
        fallback_tool="canva",
    ),
    "writesonic": ToolInfo(
        slug="writesonic",
        name="Writesonic",
        category="copy",
        min_plan="enterprise",
        cost_tier="low",
        description="SEO copy, ads, blogs, landing pages con scoring.",
        provider_module="writesonic",
        requires_api_key=True,
        fallback_tool="jasper",
    ),
    "luma": ToolInfo(
        slug="luma",
        name="Luma Dream Machine",
        category="video",
        min_plan="enterprise",
        cost_tier="medium",
        description="Video 3D y NeRF. Visualización de productos en 3D.",
        provider_module="fal_aggregator",
        requires_api_key=True,
        fallback_tool="runway",
    ),
    "custom_api": ToolInfo(
        slug="custom_api",
        name="Custom API Key",
        category="custom",
        min_plan="enterprise",
        cost_tier="variable",
        description="Trae tu propia API key de cualquier proveedor.",
        provider_module="",
        requires_api_key=True,
        fallback_tool="",
    ),
}


# ============================================================================
# MAPEO POR PLAN
# ============================================================================

PLAN_CONTENT_TOOLS: Dict[str, List[str]] = {
    "free": [
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "kimi", "ollama",
    ],
    "starter": [
        # Hereda todo de free
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "kimi", "ollama",
        # Nuevas
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
    ],
    "pro": [
        # Hereda todo de starter
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "kimi", "ollama",
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
        # Nuevas
        "midjourney", "runway", "heygen", "pika",
        "elevenlabs", "gamma",
    ],
    "enterprise": [
        # Hereda todo de pro
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "kimi", "ollama",
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
        "midjourney", "runway", "heygen", "pika",
        "elevenlabs", "gamma",
        # Nuevas
        "seedance", "kling", "sora", "sd35",
        "adcreative", "writesonic", "luma", "custom_api",
    ],
}


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def get_tools_for_plan(plan_tier: str) -> List[str]:
    """Retorna lista de slugs de herramientas disponibles para un plan."""
    return PLAN_CONTENT_TOOLS.get(plan_tier, PLAN_CONTENT_TOOLS["free"])


def get_tool_info(slug: str) -> ToolInfo:
    """Retorna metadatos de una herramienta."""
    return TOOL_REGISTRY.get(slug)


def is_tool_allowed(tool_slug: str, plan_tier: str) -> bool:
    """Verifica si una herramienta está permitida para un plan."""
    allowed = set(get_tools_for_plan(plan_tier))
    return tool_slug in allowed


def get_tools_by_category(plan_tier: str, category: str) -> List[ToolInfo]:
    """Filtra herramientas por categoría para un plan."""
    allowed_slugs = set(get_tools_for_plan(plan_tier))
    return [
        tool for slug, tool in TOOL_REGISTRY.items()
        if slug in allowed_slugs and tool.category == category
    ]


def get_fallback_tool(tool_slug: str, plan_tier: str) -> str:
    """Obtiene herramienta fallback permitida para el plan."""
    tool = TOOL_REGISTRY.get(tool_slug)
    if not tool:
        return ""

    # Si el fallback está permitido, úsalo
    if tool.fallback_tool and is_tool_allowed(tool.fallback_tool, plan_tier):
        return tool.fallback_tool

    # Buscar cualquier herramienta de la misma categoría permitida
    category_tools = get_tools_by_category(plan_tier, tool.category)
    if category_tools:
        return category_tools[0].slug

    return ""


def get_plan_upgrade_message(tool_slug: str, current_plan: str) -> str:
    """Genera mensaje amigable sugiriendo upgrade."""
    tool = TOOL_REGISTRY.get(tool_slug)
    if not tool:
        return f"La herramienta '{tool_slug}' no está disponible."

    plans = ["free", "starter", "pro", "enterprise"]
    current_idx = plans.index(current_plan) if current_plan in plans else 0
    required_idx = plans.index(tool.min_plan)

    if required_idx <= current_idx:
        return f"La herramienta '{tool.name}' debería estar disponible en tu plan."

    required_plan = plans[required_idx]
    return (
        f"🚀 '{tool.name}' requiere el plan {required_plan.upper()}. "
        f"Tu plan actual es {current_plan.upper()}. "
        f"Actualiza para desbloquear {tool.description}"
    )


def get_tools_pricing_table() -> Dict[str, Dict]:
    """Genera tabla de precios para la UI."""
    table = {}
    for slug, tool in TOOL_REGISTRY.items():
        table[slug] = {
            "name": tool.name,
            "category": tool.category,
            "min_plan": tool.min_plan,
            "cost_tier": tool.cost_tier,
            "description": tool.description,
        }
    return table


def get_plan_comparison() -> Dict[str, Dict]:
    """Genera comparación de planes para la UI."""
    comparison = {}
    for plan in ["free", "starter", "pro", "enterprise"]:
        tools = get_tools_for_plan(plan)
        by_category = {}
        for slug in tools:
            tool = TOOL_REGISTRY.get(slug)
            if tool:
                by_category.setdefault(tool.category, []).append(tool.name)
        comparison[plan] = {
            "tool_count": len(tools),
            "tools_by_category": by_category,
            "tool_slugs": tools,
        }
    return comparison
