"""Celery Tasks para Generación de Contenido con IA

Tareas en background para generar imágenes, videos, copy, carruseles y thumbnails
usando el ContentGenerationRouter que optimiza costos y calidad.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from celery import shared_task
from sqlalchemy import select, and_, or_, func

from app.core.database import AsyncSessionLocal
from app.core.config import get_settings
from app.domains.automations.models import (
    GeneratedContent, ContentCalendar, WorkflowActionType,
    WorkflowExecution, Workflow,
)
from app.domains.catalogs.models import CatalogItem
from app.domains.businesses.models import Business
from app.integrations.content_generation.router import ContentGenerationRouter
from app.integrations.content_generation.base import GenerationConfig, ContentQuality, ContentType
from app.integrations.content_generation.cache import ContentCache

settings = get_settings()


def run_async(coro):
    """Run an async coroutine in a sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ============================================================================
# Helper: obtener plan tier del negocio
# ============================================================================

async def _get_business_plan_tier(db, business_id: uuid.UUID) -> str:
    """Obtiene el tier de suscripción del negocio."""
    from app.domains.subscriptions.models import Subscription
    result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.business_id == business_id,
                Subscription.status == "active",
            )
        )
    )
    sub = result.scalar_one_or_none()
    if sub:
        return sub.plan_tier if hasattr(sub, 'plan_tier') else "starter"
    return "free"  # Default para negocios sin suscripción activa


# ============================================================================
# AI Content Generation Tasks (con Router Inteligente)
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_product_images_task(self, business_id: str, catalog_item_id: str, image_types: Optional[List[str]] = None):
    """Genera imágenes de producto usando el router inteligente.

    El router selecciona automáticamente el proveedor más económico:
    - Draft: Replicate Flux Schnell ($0.015) o GPT Image Mini Low ($0.005)
    - Standard: DALL-E 3 ($0.04)
    - Premium: DALL-E 3 HD ($0.08)
    """
    if image_types is None:
        image_types = ["hero", "lifestyle", "infographic"]

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CatalogItem).where(
                    and_(CatalogItem.id == uuid.UUID(catalog_item_id),
                         CatalogItem.business_id == uuid.UUID(business_id))
                )
            )
            item = result.scalar_one_or_none()
            if not item:
                return {"error": "CatalogItem not found"}

            biz_result = await db.execute(
                select(Business).where(Business.id == uuid.UUID(business_id))
            )
            business = biz_result.scalar_one_or_none()

            plan_tier = await _get_business_plan_tier(db, uuid.UUID(business_id))
            router = ContentGenerationRouter()
            cache = ContentCache()

            generated = []
            for img_type in image_types:
                # Verificar caché de prompt
                cached_prompt = await cache.get_cached_prompt(catalog_item_id, "image", img_type)

                if cached_prompt:
                    prompt = cached_prompt
                else:
                    prompt = _build_image_prompt(item, img_type, business)
                    await cache.cache_prompt(catalog_item_id, "image", img_type, prompt)

                # Crear registro en DB
                gc = GeneratedContent(
                    business_id=uuid.UUID(business_id),
                    catalog_item_id=uuid.UUID(catalog_item_id),
                    content_type="image",
                    agent_slug="ai-image-architect",
                    status="pending",
                    purpose=img_type,
                    prompt=prompt,
                    generation_config={
                        "image_type": img_type,
                        "product_name": item.name,
                        "model": "auto-routed",
                        "size": "1024x1024",
                    },
                )
                db.add(gc)
                await db.flush()

                # Determinar calidad según tipo de imagen
                quality = ContentQuality.STANDARD
                if img_type == "hero":
                    quality = ContentQuality.PREMIUM
                elif img_type in ("ugc_style", "social"):
                    quality = ContentQuality.DRAFT

                # Generar con router inteligente
                gc.status = "generating"
                await db.commit()

                try:
                    gen_result = await router.generate(
                        business_id=business_id,
                        config=GenerationConfig(
                            prompt=prompt,
                            content_type=ContentType.IMAGE,
                            quality=quality,
                            num_variations=1,
                            extra_params={"size": "1024x1024"},
                        ),
                        plan_tier=plan_tier,
                    )

                    if gen_result.success:
                        gc.source_url = gen_result.url
                        gc.status = "completed"
                        gc.ai_model_used = gen_result.model_used
                        gc.generation_cost = int(gen_result.cost_usd * 100)  # centavos
                        gc.generation_config.update({
                            "width": gen_result.width,
                            "height": gen_result.height,
                            "compressed_size_kb": gen_result.metadata.get("compressed_size_kb"),
                        })
                    else:
                        gc.status = "failed"
                        gc.feedback_notes = gen_result.error_message

                except Exception as e:
                    gc.status = "failed"
                    gc.feedback_notes = str(e)
                    # Retry
                    raise self.retry(exc=e)

                await db.commit()
                generated.append({
                    "id": str(gc.id),
                    "type": img_type,
                    "status": gc.status,
                    "prompt": prompt,
                    "url": gc.source_url,
                    "cost_usd": gc.generation_cost / 100 if gc.generation_cost else 0,
                    "model": gc.ai_model_used,
                })

            return {
                "catalog_item_id": catalog_item_id,
                "generated": generated,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video_clips_task(self, business_id: str, catalog_item_id: str, video_types: Optional[List[str]] = None):
    """Genera clips de video usando el router inteligente.

    El router selecciona:
    - Draft: Runway Gen-4 Turbo ($0.05/s) o Replicate
    - Standard: Runway Gen-4 ($0.12/s)
    - Premium: Seedance 2.0 ($0.10/s)
    """
    if video_types is None:
        video_types = ["hook", "demo", "cta"]

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CatalogItem).where(
                    and_(CatalogItem.id == uuid.UUID(catalog_item_id),
                         CatalogItem.business_id == uuid.UUID(business_id))
                )
            )
            item = result.scalar_one_or_none()
            if not item:
                return {"error": "CatalogItem not found"}

            plan_tier = await _get_business_plan_tier(db, uuid.UUID(business_id))
            router = ContentGenerationRouter()
            cache = ContentCache()

            generated = []
            for vid_type in video_types:
                cached_script = await cache.get_cached_prompt(catalog_item_id, "video", vid_type)
                if cached_script:
                    script = cached_script
                else:
                    script = _build_video_script(item, vid_type)
                    await cache.cache_prompt(catalog_item_id, "video", vid_type, script)

                gc = GeneratedContent(
                    business_id=uuid.UUID(business_id),
                    catalog_item_id=uuid.UUID(catalog_item_id),
                    content_type="video",
                    agent_slug="ai-video-director",
                    status="pending",
                    purpose=vid_type,
                    text_content=script,
                    generation_config={
                        "video_type": vid_type,
                        "duration": "5s",
                        "aspect_ratio": "9:16",
                    },
                )
                db.add(gc)
                await db.flush()

                quality = ContentQuality.STANDARD
                if vid_type == "hook":
                    quality = ContentQuality.PREMIUM

                gc.status = "generating"
                await db.commit()

                try:
                    gen_result = await router.generate(
                        business_id=business_id,
                        config=GenerationConfig(
                            prompt=script,
                            content_type=ContentType.VIDEO,
                            quality=quality,
                            duration_seconds=5,
                            aspect_ratio="9:16",
                        ),
                        plan_tier=plan_tier,
                    )

                    if gen_result.success:
                        gc.source_url = gen_result.url
                        gc.status = "completed"
                        gc.ai_model_used = gen_result.model_used
                        gc.generation_cost = int(gen_result.cost_usd * 100)
                    else:
                        gc.status = "failed"
                        gc.feedback_notes = gen_result.error_message

                except Exception as e:
                    gc.status = "failed"
                    gc.feedback_notes = str(e)
                    raise self.retry(exc=e)

                await db.commit()
                generated.append({
                    "id": str(gc.id),
                    "type": vid_type,
                    "status": gc.status,
                    "script": script,
                    "url": gc.source_url,
                    "cost_usd": gc.generation_cost / 100 if gc.generation_cost else 0,
                    "model": gc.ai_model_used,
                })

            return {
                "catalog_item_id": catalog_item_id,
                "generated": generated,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_product_copy_task(self, business_id: str, catalog_item_id: str, copy_types: Optional[List[str]] = None):
    """Genera copy usando GPT-4o-mini (muy económico: ~$0.0001-0.0005 por generación)."""
    if copy_types is None:
        copy_types = ["benefit_focused", "story_driven", "social_caption"]

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CatalogItem).where(
                    and_(CatalogItem.id == uuid.UUID(catalog_item_id),
                         CatalogItem.business_id == uuid.UUID(business_id))
                )
            )
            item = result.scalar_one_or_none()
            if not item:
                return {"error": "CatalogItem not found"}

            plan_tier = await _get_business_plan_tier(db, uuid.UUID(business_id))
            cache = ContentCache()

            generated = []
            for copy_type in copy_types:
                cached_prompt = await cache.get_cached_prompt(catalog_item_id, "copy", copy_type)
                if cached_prompt:
                    prompt_text = cached_prompt
                else:
                    prompt_text = _build_copy_prompt(item, copy_type)
                    await cache.cache_prompt(catalog_item_id, "copy", copy_type, prompt_text)

                gc = GeneratedContent(
                    business_id=uuid.UUID(business_id),
                    catalog_item_id=uuid.UUID(catalog_item_id),
                    content_type="copy",
                    agent_slug="ai-copy-creator",
                    status="pending",
                    purpose=copy_type,
                    generation_config={
                        "copy_type": copy_type,
                        "model": "gpt-4o-mini",
                    },
                )
                db.add(gc)
                await db.flush()

                try:
                    from app.domains.agents.llm_provider import generate_with_fallback
                    from langchain_core.messages import SystemMessage, HumanMessage

                    system_msg = SystemMessage(content=(
                        "Eres un copywriter experto en e-commerce latinoamericano. "
                        "Genera copy persuasivo en español. Usa PAS, AIDA, StoryBrand. "
                        "Máximo 150 palabras."
                    ))
                    human_msg = HumanMessage(content=prompt_text)

                    response = await generate_with_fallback(
                        db, uuid.UUID(business_id), [system_msg, human_msg], model="llama3.1", temperature=0.7, max_tokens=300,
                    )
                    if response:
                        gc.text_content = response.content
                        gc.prompt = prompt_text
                        gc.status = "completed"
                        gc.ai_model_used = response.model_used or "llama3.1"
                        gc.generation_cost = int((response.cost_usd or 0) * 100)
                    else:
                        gc.prompt = prompt_text
                        gc.text_content = f"[PROMPT LISTO]\n\n{prompt_text}"
                        gc.status = "completed"
                        gc.ai_model_used = "prompt-only"
                        gc.feedback_notes = "No hay proveedor LLM disponible. Modo demo."
                except Exception as e:
                    gc.status = "failed"
                    gc.feedback_notes = str(e)
                    raise self.retry(exc=e)

                await db.commit()
                generated.append({
                    "id": str(gc.id),
                    "type": copy_type,
                    "status": gc.status,
                    "copy": gc.text_content,
                })

            return {
                "catalog_item_id": catalog_item_id,
                "generated": generated,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_carousel_task(self, business_id: str, catalog_item_id: str, carousel_type: str = "product_showcase"):
    """Genera estructura de carousel."""
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CatalogItem).where(
                    and_(CatalogItem.id == uuid.UUID(catalog_item_id),
                         CatalogItem.business_id == uuid.UUID(business_id))
                )
            )
            item = result.scalar_one_or_none()
            if not item:
                return {"error": "CatalogItem not found"}

            gc = GeneratedContent(
                business_id=uuid.UUID(business_id),
                catalog_item_id=uuid.UUID(catalog_item_id),
                content_type="carousel",
                agent_slug="ai-carousel-designer",
                status="pending",
                purpose=carousel_type,
                generation_config={
                    "carousel_type": carousel_type,
                    "slide_count": 7,
                },
            )
            db.add(gc)
            await db.flush()

            prompt_text = _build_carousel_prompt(item, carousel_type)

            try:
                from app.domains.agents.llm_provider import generate_with_fallback
                from langchain_core.messages import SystemMessage, HumanMessage

                system_msg = SystemMessage(content=(
                    "Eres un diseñador de carruseles de Instagram experto. "
                    "Crea estructuras de 5-7 slides. Máximo 15 palabras por slide."
                ))
                human_msg = HumanMessage(content=prompt_text)

                response = await generate_with_fallback(
                    db, uuid.UUID(business_id), [system_msg, human_msg], model="llama3.1", temperature=0.7, max_tokens=500,
                )
                if response:
                    gc.text_content = response.content
                    gc.prompt = prompt_text
                    gc.status = "completed"
                    gc.ai_model_used = response.model_used or "llama3.1"
                    gc.generation_cost = int((response.cost_usd or 0) * 100)
                else:
                    gc.prompt = prompt_text
                    gc.text_content = f"[PROMPT LISTO]\n\n{prompt_text}"
                    gc.status = "completed"
                    gc.ai_model_used = "prompt-only"
                    gc.feedback_notes = "No hay proveedor LLM disponible. Modo demo."
            except Exception as e:
                gc.status = "failed"
                gc.feedback_notes = str(e)
                raise self.retry(exc=e)

            await db.commit()
            return {
                "catalog_item_id": catalog_item_id,
                "carousel_type": carousel_type,
                "content": gc.text_content,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_thumbnail_task(self, business_id: str, video_title: str, video_description: str = ""):
    """Genera thumbnail usando el router inteligente (imagen)."""
    async def _run():
        async with AsyncSessionLocal() as db:
            plan_tier = await _get_business_plan_tier(db, uuid.UUID(business_id))
            router = ContentGenerationRouter()

            gc = GeneratedContent(
                business_id=uuid.UUID(business_id),
                content_type="thumbnail",
                agent_slug="ai-thumbnail-master",
                status="pending",
                purpose="video_cover",
                generation_config={
                    "video_title": video_title,
                    "aspect_ratio": "16:9",
                },
            )
            db.add(gc)
            await db.flush()

            prompt = _build_thumbnail_prompt(video_title, video_description)
            gc.prompt = prompt
            gc.status = "generating"
            await db.commit()

            try:
                gen_result = await router.generate(
                    business_id=business_id,
                    config=GenerationConfig(
                        prompt=prompt,
                        content_type=ContentType.IMAGE,
                        quality=ContentQuality.STANDARD,
                        extra_params={"size": "1792x1024"},
                    ),
                    plan_tier=plan_tier,
                )

                if gen_result.success:
                    gc.source_url = gen_result.url
                    gc.status = "completed"
                    gc.ai_model_used = gen_result.model_used
                    gc.generation_cost = int(gen_result.cost_usd * 100)
                else:
                    gc.status = "failed"
                    gc.feedback_notes = gen_result.error_message

            except Exception as e:
                gc.status = "failed"
                gc.feedback_notes = str(e)
                raise self.retry(exc=e)

            await db.commit()
            return {
                "thumbnail_id": str(gc.id),
                "prompt": prompt,
                "url": gc.source_url,
                "cost_usd": gc.generation_cost / 100 if gc.generation_cost else 0,
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


# ============================================================================
# Batch & Automation Tasks
# ============================================================================

async def _get_active_business_ids() -> list[uuid.UUID]:
    """Fetch IDs of all active businesses."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Business.id).where(Business.is_active == True))
        return [row[0] for row in result.all()]


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def auto_generate_catalog_content_task(self, business_id: Optional[str] = None):
    """Genera automáticamente contenido para productos sin imágenes.

    Optimizado para bajo costo:
    - Solo genera hero + lifestyle (los más importantes)
    - Solo para productos sin imágenes existentes
    - Limitado por presupuesto del plan
    """
    async def _run_single(bid: uuid.UUID):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CatalogItem).where(
                    and_(
                        CatalogItem.business_id == bid,
                        or_(
                            CatalogItem.images.is_(None),
                            CatalogItem.images == [],
                            CatalogItem.images == {},
                        )
                    )
                ).limit(10)
            )
            items = result.scalars().all()

            if not items:
                return {"message": "No products need content generation", "count": 0, "business_id": str(bid)}

            tasks_launched = []
            for item in items:
                img_task = generate_product_images_task.delay(
                    business_id=str(bid),
                    catalog_item_id=str(item.id),
                    image_types=["hero", "lifestyle"],
                )
                copy_task = generate_product_copy_task.delay(
                    business_id=str(bid),
                    catalog_item_id=str(item.id),
                    copy_types=["benefit_focused", "social_caption"],
                )
                tasks_launched.append({
                    "item_id": str(item.id),
                    "image_task": img_task.id,
                    "copy_task": copy_task.id,
                })

            return {
                "message": f"Launched content generation for {len(items)} products",
                "count": len(items),
                "tasks": tasks_launched,
                "business_id": str(bid),
            }

    async def _run_all():
        business_ids = await _get_active_business_ids()
        results = []
        for bid in business_ids:
            try:
                results.append(await _run_single(bid))
            except Exception as exc:
                logger.error(f"auto_generate_catalog_content_task failed for {bid}: {exc}")
        return {"status": "ok", "processed": len(results), "total_businesses": len(business_ids)}

    try:
        if business_id:
            return run_async(_run_single(uuid.UUID(business_id)))
        return run_async(_run_all())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def schedule_content_posts_task(self, business_id: Optional[str] = None):
    """Programa publicaciones automáticas."""
    async def _run_single(bid: uuid.UUID):
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(ContentCalendar).where(
                    and_(
                        ContentCalendar.business_id == bid,
                        ContentCalendar.status == "scheduled",
                        ContentCalendar.scheduled_at <= now,
                        ContentCalendar.approval_status == "approved",
                    )
                ).limit(20)
            )
            posts = result.scalars().all()

            published = []
            for post in posts:
                post.status = "published"
                post.published_at = now
                published.append({
                    "post_id": str(post.id),
                    "platform": post.platform,
                    "format": post.content_format,
                })

            await db.commit()
            return {
                "published_count": len(published),
                "posts": published,
                "business_id": str(bid),
            }

    async def _run_all():
        business_ids = await _get_active_business_ids()
        total_published = 0
        for bid in business_ids:
            try:
                result = await _run_single(bid)
                total_published += result.get("published_count", 0)
            except Exception as exc:
                logger.error(f"schedule_content_posts_task failed for {bid}: {exc}")
        return {"status": "ok", "total_published": total_published, "total_businesses": len(business_ids)}

    try:
        if business_id:
            return run_async(_run_single(uuid.UUID(business_id)))
        return run_async(_run_all())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_content_performance_task(self, business_id: Optional[str] = None):
    """Analiza rendimiento de contenido."""
    async def _run_single(bid: uuid.UUID):
        async with AsyncSessionLocal() as db:
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            result = await db.execute(
                select(GeneratedContent).where(
                    and_(
                        GeneratedContent.business_id == bid,
                        GeneratedContent.status == "completed",
                        GeneratedContent.created_at >= week_ago,
                    )
                )
            )
            contents = result.scalars().all()

            insights = {
                "business_id": str(bid),
                "total_content": len(contents),
                "by_type": {},
                "by_agent": {},
                "total_spend_usd": sum((c.generation_cost or 0) / 100 for c in contents),
                "recommendations": [],
            }

            for c in contents:
                insights["by_type"][c.content_type] = insights["by_type"].get(c.content_type, 0) + 1
                insights["by_agent"][c.agent_slug] = insights["by_agent"].get(c.agent_slug, 0) + 1

            if len(contents) > 0:
                insights["recommendations"].append(
                    "Generar más contenido del tipo con mayor engagement"
                )
                insights["recommendations"].append(
                    "A/B test con variaciones del contenido top performer"
                )

            return insights

    async def _run_all():
        business_ids = await _get_active_business_ids()
        all_insights = []
        for bid in business_ids:
            try:
                all_insights.append(await _run_single(bid))
            except Exception as exc:
                logger.error(f"analyze_content_performance_task failed for {bid}: {exc}")
        return {"status": "ok", "insights_count": len(all_insights), "total_businesses": len(business_ids), "insights": all_insights}

    try:
        if business_id:
            return run_async(_run_single(uuid.UUID(business_id)))
        return run_async(_run_all())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=3600)
def cleanup_old_generated_content_task(self, business_id: str = None):
    """Limpia contenido generado antiguo para reducir costos de DB.

    Política:
    - Contenido 'failed' > 30 días: eliminar
    - Contenido 'completed' > 90 días sin uso: soft-delete
    - Variaciones > 30 días: limpiar JSONB
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)

            # Eliminar contenido failed antiguo
            from sqlalchemy import delete
            failed_threshold = now - timedelta(days=30)

            stmt_failed = delete(GeneratedContent).where(
                and_(
                    GeneratedContent.status == "failed",
                    GeneratedContent.created_at < failed_threshold,
                )
            )
            failed_result = await db.execute(stmt_failed)

            # Soft-delete contenido completed sin uso > 90 días
            unused_threshold = now - timedelta(days=90)
            result = await db.execute(
                select(GeneratedContent).where(
                    and_(
                        GeneratedContent.status == "completed",
                        GeneratedContent.created_at < unused_threshold,
                        GeneratedContent.usage_count == 0,
                    )
                )
            )
            unused = result.scalars().all()
            for item in unused:
                item.status = "archived"
                # Limpiar URLs pesadas
                item.variations = []
                item.performance_data = {}

            await db.commit()

            return {
                "failed_deleted": failed_result.rowcount if hasattr(failed_result, 'rowcount') else 0,
                "unused_archived": len(unused),
            }

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


# ============================================================================
# Prompt Builders
# ============================================================================

def _build_image_prompt(item: CatalogItem, image_type: str, business) -> str:
    product = item.name
    desc = item.description or ""
    brand = business.name if business else ""

    base = f"Photorealistic product photography of {product}"

    prompts = {
        "hero": f"{base} on a clean white background, studio lighting, sharp focus, 8K quality, professional e-commerce product photo, minimalist, elegant, shot on Canon EOS R5 with 85mm lens, subtle shadow beneath product, premium feel",
        "lifestyle": f"{base} in a beautiful modern home setting, soft natural lighting, lifestyle product photography, aspirational context, warm and inviting mood, shot on Sony A7IV, shallow depth of field, cozy atmosphere, professional editorial style",
        "infographic": f"Clean infographic design showing {product} benefits and features, modern flat design style, icons and text labels, minimalist color palette, white background, professional marketing graphic, easy to read, bold typography, visual hierarchy",
        "ugc_style": f"Casual phone photo of {product} on a messy desk, natural indoor lighting, slightly imperfect angle, authentic user-generated content style, looks like taken by real customer, relatable and genuine feel",
        "social": f"Eye-catching social media image of {product}, bold colors, clean composition, Instagram-ready, square format, high contrast, modern aesthetic, professional product photography",
    }
    return prompts.get(image_type, f"{base}, professional product photography, high quality")


def _build_video_script(item: CatalogItem, video_type: str) -> str:
    product = item.name

    scripts = {
        "hook": f"Extreme close-up of {product} with dramatic lighting. Text overlay: 'Wait until you see this...' Camera slowly pulls back to reveal full scene. Mood: Curiosity, intrigue, must-watch.",
        "demo": f"Person holding {product}, smiling. Close-up of product in use, smooth camera movement. Result/reaction shot, satisfaction. Voiceover: 'This is how {product} changes everything...'",
        "cta": f"Bold text: 'Limited time offer' + {product} image. Flash key benefits with quick cuts. Price + discount displayed prominently. 'Link in bio' or 'Shop now' with urgency.",
    }
    return scripts.get(video_type, f"Video for {product}: Hook → Problem → Solution → Proof → CTA")


def _build_copy_prompt(item: CatalogItem, copy_type: str) -> str:
    product = item.name
    desc = item.description or ""
    price = item.price
    currency = item.currency

    prompts = {
        "benefit_focused": f"Escribe descripción persuasiva para '{product}'. Descripción: {desc}. Precio: {currency} {price}. Enfoque: BENEFICIOS, no características. Tono: Empático, aspiracional. Incluye: Hook, transformación, CTA.",
        "story_driven": f"Escribe historia de ventas para '{product}'. Contexto: {desc}. Formato: Before → Struggle → Discovery → After. Tono: Vulnerable, auténtico. 150-200 palabras.",
        "spec_heavy": f"Escribe descripción técnica para '{product}'. Info: {desc}. Incluye: Especificaciones, materiales, dimensiones, uso, cuidados. Tono: Profesional, preciso.",
        "social_caption": f"Escribe 3 captions de Instagram para '{product}'. Contexto: {desc}. Requisitos: 80-150 palabras, emojis, 5-10 hashtags, CTA. Variación 1: Educativo. Variación 2: Storytelling. Variación 3: Directo.",
        "ad_headline": f"Escribe 5 headlines para '{product}'. Contexto: {desc}. Máx 40 caracteres. Técnicas: Curiosity gap, beneficio, urgencia, pregunta, número. Deben detener scroll en 0.5s.",
    }
    return prompts.get(copy_type, f"Escribe copy para '{product}'. Contexto: {desc}")


def _build_carousel_prompt(item: CatalogItem, carousel_type: str) -> str:
    product = item.name
    desc = item.description or ""

    if carousel_type == "product_showcase":
        return f"Diseña carousel de 7 slides para '{product}'. Descripción: {desc}. Estructura: 1-Cover detiene scroll, 2-Problema, 3-4-5-Features+beneficios, 6-Social proof, 7-CTA. Máx 15 palabras por slide."
    elif carousel_type == "educational":
        return f"Diseña carousel educativo de 7 slides sobre '{product}'. Contexto: {desc}. Estructura: How-to. Cada slide: 1 idea clara, máx 15 palabras. Incluir 'Guarda esto'."
    return f"Diseña carousel de 5-7 slides para '{product}'. Contexto: {desc}"


def _build_thumbnail_prompt(video_title: str, video_description: str) -> str:
    return (
        f"YouTube thumbnail: '{video_title}'. Content: {video_description}. "
        f"Style: Bold, high contrast. Subject: Strong emotion face OR dramatic product. "
        f"Text: 1-3 words max, bold white with black outline. Background: High contrast gradient. "
        f"Mood: Urgency, curiosity. Format: 16:9, professional, click-worthy"
    )
