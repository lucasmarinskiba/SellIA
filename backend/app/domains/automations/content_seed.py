"""Seed pre-built content generation automations.

Workflows para generación automática de contenido con IA:
- Auto-generar imágenes para productos nuevos
- Auto-generar copy/descripciones
- Auto-generar carruseles
- Auto-generar videos demo
- Auto-generar thumbnails
- Auto-actualizar catálogo con contenido generado
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.automations.models import (
    Workflow, WorkflowTriggerType, WorkflowActionType, WorkflowStatus,
)


async def get_or_create_workflow(db: AsyncSession, business_id: uuid.UUID, name: str, **defaults) -> Workflow:
    result = await db.execute(
        select(Workflow).where(Workflow.business_id == business_id, Workflow.name == name)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        wf = Workflow(business_id=business_id, name=name, **defaults)
        db.add(wf)
        await db.flush()
    return wf


async def seed_content_automations(db: AsyncSession, business_id: uuid.UUID):
    """Seed content generation workflows for a business."""

    content_workflows = [
        {
            "name": "🖼️ Auto-Generar Imágenes de Producto",
            "description": "Cuando se crea un producto sin imágenes, genera automáticamente hero, lifestyle e infographic vía IA.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "new_catalog_item", "requires_images": True},
            "actions": [
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["hero", "lifestyle", "infographic"],
                    "model": "dall-e-3",
                    "quality": "premium",
                }},
                {"type": WorkflowActionType.UPDATE_CATALOG_MEDIA, "config": {
                    "attach_to_catalog": True,
                    "set_as_primary": True,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "✍️ Auto-Generar Descripción de Producto",
            "description": "Genera 3 descripciones (benefits, story, specs) para cada producto nuevo vía IA.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "new_catalog_item", "requires_description": True},
            "actions": [
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-copy-creator",
                    "copy_types": ["benefit_focused", "story_driven", "spec_heavy"],
                    "language": "es",
                    "max_words": 150,
                }},
                {"type": WorkflowActionType.UPDATE_CATALOG_MEDIA, "config": {
                    "update_description": True,
                    "select_best": True,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🎠 Auto-Generar Carrusel de Producto",
            "description": "Genera un carousel de 7 slides para Instagram cada vez que se lanza un producto nuevo.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "product_launch"},
            "actions": [
                {"type": WorkflowActionType.GENERATE_CAROUSEL, "config": {
                    "agent": "ai-carousel-designer",
                    "carousel_type": "product_showcase",
                    "slide_count": 7,
                    "platform": "instagram",
                }},
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["carousel_cover"],
                    "platform": "instagram",
                }},
                {"type": WorkflowActionType.SCHEDULE_POST, "config": {
                    "platform": "instagram",
                    "format": "carousel",
                    "auto_publish": False,
                    "requires_approval": True,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🎬 Auto-Generar Video Demo",
            "description": "Genera clips de video (hook, demo, CTA) para productos de alto valor.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "high_value_product", "min_price": 100},
            "actions": [
                {"type": WorkflowActionType.GENERATE_VIDEO, "config": {
                    "agent": "ai-video-director",
                    "video_types": ["hook", "demo", "cta"],
                    "duration": "5s",
                    "aspect_ratio": "9:16",
                }},
                {"type": WorkflowActionType.GENERATE_THUMBNAIL, "config": {
                    "agent": "ai-thumbnail-master",
                    "platform": "reels",
                }},
                {"type": WorkflowActionType.SCHEDULE_POST, "config": {
                    "platform": "instagram",
                    "format": "reel",
                    "auto_publish": False,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "📱 Auto-Generar Contenido Semanal",
            "description": "Genera automáticamente 3 Reels, 2 carruseles y 5 posts semanales basados en el catálogo.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"schedule": "weekly", "day": "monday", "hour": 9},
            "actions": [
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-copy-creator",
                    "copy_types": ["social_caption", "ad_headline"],
                    "quantity": 10,
                }},
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["social_post", "story_background"],
                    "quantity": 5,
                }},
                {"type": WorkflowActionType.GENERATE_CAROUSEL, "config": {
                    "agent": "ai-carousel-designer",
                    "carousel_type": "educational",
                    "quantity": 2,
                }},
                {"type": WorkflowActionType.SCHEDULE_POST, "config": {
                    "platform": "instagram",
                    "format": "mixed",
                    "auto_publish": False,
                    "spread_over_week": True,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🎯 Auto-Generar Creativos de Ads",
            "description": "Genera automáticamente 5 variaciones de anuncio (imagen + copy + CTA) para campañas activas.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"schedule": "weekly", "day": "wednesday", "hour": 10},
            "actions": [
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-ad-creative",
                    "copy_types": ["ad_headline", "ad_body", "ad_cta"],
                    "variations": 5,
                }},
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["ad_image"],
                    "variations": 5,
                    "platform": "meta_ads",
                }},
                {"type": WorkflowActionType.GENERATE_THUMBNAIL, "config": {
                    "agent": "ai-thumbnail-master",
                    "variations": 3,
                }},
                {"type": WorkflowActionType.CREATE_CONTENT_BRIEF, "config": {
                    "agent": "ai-content-orchestrator",
                    "brief_type": "ad_campaign",
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🛍️ Auto-Actualizar Catálogo con IA",
            "description": "Cuando se actualiza un producto, regenera automáticamente imágenes y copy si han pasado 30 días.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "catalog_updated", "max_age_days": 30},
            "actions": [
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["hero", "lifestyle"],
                    "refresh_existing": True,
                }},
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-copy-creator",
                    "copy_types": ["benefit_focused"],
                    "refresh_existing": True,
                }},
                {"type": WorkflowActionType.UPDATE_CATALOG_MEDIA, "config": {
                    "replace_old": False,
                    "add_as_variant": True,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "📧 Auto-Generar Email de Lanzamiento",
            "description": "Genera email completo de lanzamiento con copy + banner + CTA para lista de suscriptores.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "product_launch"},
            "actions": [
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-email-creative",
                    "copy_types": ["launch_email"],
                    "include_subject": True,
                    "subject_variations": 5,
                }},
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-image-architect",
                    "image_types": ["email_banner"],
                    "dimensions": "600x300",
                }},
                {"type": WorkflowActionType.GENERATE_THUMBNAIL, "config": {
                    "agent": "ai-thumbnail-master",
                    "purpose": "email_preview",
                }},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {
                    "sequence": "launch_sequence",
                    "delay_hours": 0,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🎨 Auto-Generar Brand Kit",
            "description": "Genera logo concepts, paleta de colores y tipografía basado en el nombre del negocio.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"schedule": "once", "trigger": "onboarding_complete"},
            "actions": [
                {"type": WorkflowActionType.GENERATE_IMAGE, "config": {
                    "agent": "ai-brand-stylist",
                    "image_types": ["logo_concept", "mood_board"],
                    "variations": 5,
                }},
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-brand-stylist",
                    "copy_types": ["brand_guidelines", "color_palette", "typography"],
                }},
                {"type": WorkflowActionType.CREATE_CONTENT_BRIEF, "config": {
                    "agent": "ai-brand-stylist",
                    "brief_type": "brand_kit",
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "📱 Auto-Reels desde Productos",
            "description": "Genera automáticamente Reels virales (hook + demo + CTA) para cada producto del catálogo.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"schedule": "daily", "hour": 10},
            "actions": [
                {"type": WorkflowActionType.GENERATE_VIDEO, "config": {
                    "agent": "ai-reel-engineer",
                    "video_types": ["hook", "demo", "cta"],
                    "duration": "15s",
                    "aspect_ratio": "9:16",
                }},
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "ai-reel-engineer",
                    "copy_types": ["reel_caption", "hashtags", "cta"],
                }},
                {"type": WorkflowActionType.GENERATE_THUMBNAIL, "config": {
                    "agent": "ai-thumbnail-master",
                    "platform": "reels",
                }},
                {"type": WorkflowActionType.SCHEDULE_POST, "config": {
                    "platform": "instagram",
                    "format": "reel",
                    "auto_publish": False,
                }},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
    ]

    for wf_data in content_workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    await db.commit()
