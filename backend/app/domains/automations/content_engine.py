"""Content Generation Engine

Implements the 8 missing workflow action types for autonomous content creation.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.automations.models import GeneratedContent, ContentCalendar, WorkflowExecution
from app.domains.catalogs.models import CatalogItem
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger

logger = get_logger(__name__)


class ContentGenerationRouter:
    """Routes content generation requests to appropriate handlers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_image(self, business_id: uuid.UUID, prompt: str, catalog_item_id: uuid.UUID | None = None) -> Optional[GeneratedContent]:
        """Generate product image using AI."""
        content = GeneratedContent(
            business_id=business_id,
            catalog_item_id=catalog_item_id,
            content_type="image",
            status="pending",
            prompt=prompt,
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        # In production, this would call DALL-E / Stable Diffusion API
        # For now, mark as completed with placeholder
        content.status = "completed"
        content.text_content = f"[IMAGE_GENERATED: {prompt[:100]}...]"
        await self.db.commit()

        logger.info(f"Generated image content {content.id} for business {business_id}")
        return content

    async def generate_video(self, business_id: uuid.UUID, script: str, catalog_item_id: uuid.UUID | None = None) -> Optional[GeneratedContent]:
        """Generate video script and thumbnail."""
        content = GeneratedContent(
            business_id=business_id,
            catalog_item_id=catalog_item_id,
            content_type="video",
            status="pending",
            prompt=script,
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        # Generate thumbnail text
        thumbnail = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt="Eres un experto en thumbnails para videos de ventas. Generas títulos cortos y hooks visuales.",
            user_prompt=f"Genera un thumbnail hook para este video: {script[:200]}",
            max_tokens=100,
        )

        content.status = "completed"
        content.text_content = f"Script: {script[:500]}\n\nThumbnail: {thumbnail or 'N/A'}"
        await self.db.commit()

        return content

    async def generate_copy(self, business_id: uuid.UUID, product_name: str, product_description: str, tone: str = "persuasive") -> Optional[GeneratedContent]:
        """Generate sales copy."""
        content = GeneratedContent(
            business_id=business_id,
            content_type="copy",
            status="pending",
            prompt=f"Copy para {product_name}: {product_description}",
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        copy = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt=f"Eres un copywriter experto en ventas. Tono: {tone}. Generas copy que convierte.",
            user_prompt=f"Genera copy de ventas para: {product_name}\nDescripción: {product_description}\n\nIncluye: headline, body (2-3 oraciones), CTA.",
            max_tokens=800,
        )

        content.status = "completed"
        content.text_content = copy or "Error generando copy"
        await self.db.commit()

        return content

    async def generate_carousel(self, business_id: uuid.UUID, topic: str, slides: int = 5) -> Optional[GeneratedContent]:
        """Generate Instagram carousel structure."""
        content = GeneratedContent(
            business_id=business_id,
            content_type="carousel",
            status="pending",
            prompt=f"Carousel de {slides} slides sobre: {topic}",
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        carousel = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt="Eres un experto en carruseles de Instagram. Generas estructuras de slides que enganchan y educan.",
            user_prompt=f"Genera un carousel de {slides} slides sobre: {topic}\n\nPara cada slide: título (máx 5 palabras) + copy (máx 2 oraciones). Slide 1 = hook. Slide {slides} = CTA.",
            max_tokens=1200,
        )

        content.status = "completed"
        content.text_content = carousel or "Error generando carousel"
        await self.db.commit()

        return content

    async def generate_thumbnail(self, business_id: uuid.UUID, video_title: str) -> Optional[GeneratedContent]:
        """Generate video thumbnail concept."""
        content = GeneratedContent(
            business_id=business_id,
            content_type="thumbnail",
            status="pending",
            prompt=f"Thumbnail para: {video_title}",
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        thumbnail = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt="Eres un experto en thumbnails de YouTube/Reels. Generas conceptos visuales de alto CTR.",
            user_prompt=f"Genera concepto de thumbnail para video: '{video_title}'\n\nIncluye: descripción visual, texto superpuesto (máx 5 palabras), colores dominantes.",
            max_tokens=300,
        )

        content.status = "completed"
        content.text_content = thumbnail or "Error generando thumbnail"
        await self.db.commit()

        return content

    async def schedule_post(self, business_id: uuid.UUID, content_id: uuid.UUID, platform: str, scheduled_at: datetime) -> Optional[ContentCalendar]:
        """Schedule a post to content calendar."""
        content = await self.db.get(GeneratedContent, content_id)
        if not content:
            return None

        calendar = ContentCalendar(
            business_id=business_id,
            generated_content_id=content_id,
            scheduled_at=scheduled_at,
            platform=platform,
            status="scheduled",
            content_format="feed_post",
            caption=content.text_content[:500] if content.text_content else None,
            auto_publish=False,
            requires_approval=True,
        )
        self.db.add(calendar)
        await self.db.commit()
        await self.db.refresh(calendar)

        return calendar

    async def update_catalog_media(self, business_id: uuid.UUID, catalog_item_id: uuid.UUID, content_id: uuid.UUID) -> bool:
        """Associate generated content with catalog item."""
        item = await self.db.get(CatalogItem, catalog_item_id)
        content = await self.db.get(GeneratedContent, content_id)
        if not item or not content:
            return False

        # Update item's extra_data with content reference
        extra = dict(item.extra_data or {})
        if "generated_content" not in extra:
            extra["generated_content"] = []
        extra["generated_content"].append(str(content_id))
        item.extra_data = extra

        await self.db.commit()
        return True

    async def create_content_brief(self, business_id: uuid.UUID, campaign_name: str, objectives: str) -> Optional[GeneratedContent]:
        """Generate a complete content brief."""
        content = GeneratedContent(
            business_id=business_id,
            content_type="copy",
            status="pending",
            prompt=f"Brief para campaña: {campaign_name}",
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        brief = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt="Eres un director creativo. Generas briefs de campaña completos y accionables.",
            user_prompt=f"Genera un content brief para la campaña: '{campaign_name}'\nObjetivos: {objectives}\n\nIncluye: objetivo, audiencia, mensaje clave, tono, canales, formatos, KPIs.",
            max_tokens=1500,
        )

        content.status = "completed"
        content.text_content = brief or "Error generando brief"
        await self.db.commit()

        return content


class ContentConfidenceScorer:
    """Evaluates quality of generated content for auto-approval."""

    async def score_content(self, db: AsyncSession, content_id: uuid.UUID) -> dict[str, Any]:
        """Score generated content quality. Returns score and decision."""
        content = await db.get(GeneratedContent, content_id)
        if not content or not content.text_content:
            return {"score": 0, "decision": "reject", "reason": "No content"}

        text = content.text_content

        # Heuristic scoring (in production, this would use an LLM evaluator)
        score = 0
        checks = []

        # Length check
        if len(text) > 50:
            score += 20
            checks.append("sufficient_length")

        # No placeholders
        if "[" not in text or "]" not in text:
            score += 20
            checks.append("no_placeholders")

        # Contains CTA or action
        cta_keywords = ["compra", "agenda", "contacta", "visita", "descubre", "obtén", "llama", "escribe"]
        if any(kw in text.lower() for kw in cta_keywords):
            score += 20
            checks.append("has_cta")

        # No errors
        if "error" not in text.lower() and "falló" not in text.lower():
            score += 20
            checks.append("no_errors")

        # Language quality (basic: has sentences)
        if "." in text and len(text.split(".")) >= 2:
            score += 20
            checks.append("has_structure")

        decision = "reject"
        if score >= 85:
            decision = "auto_approve"
        elif score >= 60:
            decision = "pending_approval"

        return {
            "score": score,
            "decision": decision,
            "checks": checks,
        }
