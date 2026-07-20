"""SEO Content Pipeline — Automated SEO-optimized content generation and scheduling.

Generates blog posts, guides, and articles optimized for organic search,
then schedules them for publication and tracks performance.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import GrowthCampaign, GrowthCampaignType
from app.domains.automations.models import GeneratedContent, ContentCalendar
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger

logger = get_logger(__name__)


class SEOPipeline:
    """Automated SEO content generation and scheduling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Content Generation ==========

    async def generate_blog_post(
        self,
        business_id: uuid.UUID,
        keyword: str,
        search_intent: str = "informational",  # informational, navigational, transactional, commercial
        word_count: int = 1200,
        campaign_id: uuid.UUID = None,
    ) -> GeneratedContent:
        """Generate a complete SEO-optimized blog post."""
        # Generate article
        article = await self._generate_article(business_id, keyword, search_intent, word_count)

        # Generate meta
        meta = await self._generate_meta_tags(business_id, keyword, article)

        content = GeneratedContent(
            business_id=business_id,
            content_type="blog_post",
            status="completed",
            prompt=f"Blog post about: {keyword}",
            text_content=article.get("body", ""),
            meta_data={
                "title": article.get("title", ""),
                "meta_description": meta.get("meta_description", ""),
                "keywords": [keyword] + article.get("related_keywords", []),
                "headers": article.get("headers", []),
                "search_intent": search_intent,
                "word_count": word_count,
                "schema_markup": meta.get("schema_markup", ""),
            },
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        logger.info(f"Generated SEO blog post {content.id} for keyword '{keyword}'")
        return content

    async def generate_guide(
        self,
        business_id: uuid.UUID,
        topic: str,
        difficulty: str = "beginner",  # beginner, intermediate, advanced
        campaign_id: uuid.UUID = None,
    ) -> GeneratedContent:
        """Generate a how-to guide optimized for featured snippets."""
        system_prompt = """Eres un experto en SEO y contenido educativo. Creas guías paso a paso que:
1. Aparecen en featured snippets de Google
2. Usan estructura clara (H2, H3, listas numeradas, tablas)
3. Responden la pregunta en los primeros 40-60 palabras
4. Incluyen ejemplos prácticos y actionable

Responde en JSON:
{
  "title": "Título SEO optimizado (60-70 chars)",
  "body": "Contenido completo en markdown",
  "headers": [{"level": 2, "text": "..."}, ...],
  "related_keywords": ["...", "..."],
  "snippet_answer": "Respuesta directa en 40-60 palabras"
}"""

        user_prompt = f"""Crea una guía completa sobre: {topic}

Nivel: {difficulty}

La guía debe:
- Empezar con una respuesta directa al problema (para featured snippet)
- Tener al menos 5 secciones con H2
- Incluir listas numeradas y bullets
- Tener un CTA suave al final (no agresivo)
- Ser de 1000-1500 palabras
- Incluir ejemplos reales si es posible"""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2500,
                temperature=0.7,
            )
            import json
            article = json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Failed to generate guide: {e}")
            article = {
                "title": f"Guía completa: {topic}",
                "body": f"Contenido sobre {topic}...",
                "headers": [],
                "related_keywords": [],
                "snippet_answer": f"{topic} es...",
            }

        content = GeneratedContent(
            business_id=business_id,
            content_type="guide",
            status="completed",
            prompt=f"Guide: {topic}",
            text_content=article.get("body", ""),
            meta_data={
                "title": article.get("title", ""),
                "difficulty": difficulty,
                "snippet_answer": article.get("snippet_answer", ""),
                "headers": article.get("headers", []),
                "related_keywords": article.get("related_keywords", []),
            },
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def _generate_article(
        self,
        business_id: uuid.UUID,
        keyword: str,
        search_intent: str,
        word_count: int,
    ) -> dict[str, Any]:
        """Generate article body with AI."""
        system_prompt = f"""Eres un SEO Content Strategist AI. Creas contenido que:
1. Ranka en Google (optimizado para keywords y search intent)
2. Atrae tráfico orgánico
3. Convierte lectores en leads (sin ser pushy)

Search intent: {search_intent}
- informational: educar, responder preguntas
- commercial: comparar opciones, reviews
- transactional: facilitar la compra

Responde en JSON:
{{
  "title": "Título SEO (incluye keyword naturalmente, 50-60 chars)",
  "body": "Artículo completo en markdown. Estructura: Intro -> H2 -> H3 -> Conclusión -> CTA suave",
  "headers": [{{"level": 2, "text": "..."}}, ...],
  "related_keywords": ["keyword relacionada 1", "keyword relacionada 2"],
  "snippet_answer": "Respuesta concisa para featured snippet (40-60 palabras)"
}}"""

        user_prompt = f"""Escribe un artículo SEO de {word_count} palabras sobre: {keyword}

Requisitos:
- Keyword principal: "{keyword}" (usar 3-5 veces naturalmente)
- Search intent: {search_intent}
- Estructura: Introducción hook -> 4-6 secciones H2 -> Conclusión -> CTA educativo
- Incluir: lista numerada, bullets, tabla comparativa (si aplica)
- Tono: experto pero accesible, como un mentor
- NO sonar como publicidad, sonar como ayuda genuina
- Incluir estadísticas o datos si son relevantes
- Meta descripción natural de 150-160 caracteres"""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3000,
                temperature=0.7,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            return {
                "title": keyword.title(),
                "body": f"Artículo sobre {keyword}...",
                "headers": [],
                "related_keywords": [],
                "snippet_answer": f"{keyword} es...",
            }

    async def _generate_meta_tags(
        self,
        business_id: uuid.UUID,
        keyword: str,
        article: dict,
    ) -> dict[str, Any]:
        """Generate meta description and schema markup."""
        system_prompt = "Eres un experto en on-page SEO. Generas meta tags y schema markup que mejoran CTR."
        user_prompt = f"""Genera para este artículo:
Título: {article.get('title', keyword)}
Keyword: {keyword}

Responde en JSON:
{{
  "meta_description": "Meta descripción de 150-160 chars que incluya keyword y CTA suave",
  "schema_markup": "JSON-LD Article schema básico"
}}"""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=600,
                temperature=0.5,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Meta generation failed: {e}")
            return {
                "meta_description": f"Descubre todo sobre {keyword}. Guía completa con consejos prácticos.",
                "schema_markup": "",
            }

    # ========== Scheduling ==========

    async def schedule_publication(
        self,
        content_id: uuid.UUID,
        publish_at: datetime,
        platform: str = "blog",
    ) -> ContentCalendar:
        """Schedule content for publication."""
        content = await self.db.get(GeneratedContent, content_id)
        if not content:
            raise ValueError(f"Content {content_id} not found")

        entry = ContentCalendar(
            business_id=content.business_id,
            content_id=content_id,
            platform=platform,
            status="scheduled",
            scheduled_at=publish_at,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        logger.info(f"Scheduled content {content_id} for {publish_at} on {platform}")
        return entry

    async def get_scheduled_content(
        self,
        business_id: uuid.UUID,
        platform: str = None,
    ) -> List[ContentCalendar]:
        """Get scheduled content."""
        query = select(ContentCalendar).where(
            ContentCalendar.business_id == business_id,
            ContentCalendar.status == "scheduled",
        ).order_by(ContentCalendar.scheduled_at)
        if platform:
            query = query.where(ContentCalendar.platform == platform)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========== Performance Tracking ==========

    async def get_content_performance(self, content_id: uuid.UUID) -> dict[str, Any]:
        """Get performance metrics for a piece of content."""
        content = await self.db.get(GeneratedContent, content_id)
        if not content:
            return {"error": "Content not found"}

        # Count inbound leads attributed to this content
        from app.domains.growth.models import InboundLead
        leads_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.source_detail.contains(str(content_id)),
            )
        )
        leads_generated = leads_result.scalar() or 0

        return {
            "content_id": str(content_id),
            "title": content.meta_data.get("title", "") if content.meta_data else "",
            "type": content.content_type,
            "status": content.status,
            "leads_generated": leads_generated,
            "created_at": content.created_at.isoformat() if content.created_at else None,
        }

    # ========== Batch Operations ==========

    async def generate_content_batch(
        self,
        business_id: uuid.UUID,
        keywords: List[str],
        campaign_id: uuid.UUID = None,
    ) -> List[GeneratedContent]:
        """Generate multiple pieces of SEO content."""
        contents = []
        for keyword in keywords:
            try:
                content = await self.generate_blog_post(
                    business_id=business_id,
                    keyword=keyword,
                    campaign_id=campaign_id,
                )
                contents.append(content)
            except Exception as e:
                logger.error(f"Failed to generate content for '{keyword}': {e}")
        return contents
