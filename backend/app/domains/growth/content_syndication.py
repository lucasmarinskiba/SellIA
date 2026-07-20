"""Cross-Platform Content Syndication Engine.

Takes one piece of content (blog post, tip, insight) and automatically
adapts it for multiple platforms with native formatting:
- Instagram: carousel script + caption + hashtags
- TikTok: hook + script + CTA
- LinkedIn: professional post with storytelling
- WhatsApp Status: short text + CTA
- Blog: full SEO article
- Email: newsletter format

This is "vender sin vender" at scale — one idea, infinite distribution.
"""

import uuid
from typing import Optional, Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.automations.models import GeneratedContent, ContentCalendar
from app.core.logger import get_logger

logger = get_logger(__name__)


class ContentSyndicationEngine:
    """Adapts one content piece for multiple platforms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def syndicate_content(
        self,
        business_id: uuid.UUID,
        source_content_id: uuid.UUID,
        platforms: List[str],
    ) -> Dict[str, Any]:
        """Syndicate one content piece across multiple platforms."""
        # Get source content
        source = await self.db.get(GeneratedContent, source_content_id)
        if not source:
            return {"error": "Source content not found"}

        title = source.meta_data.get("title", "") if source.meta_data else ""
        body = source.text_content or ""

        results = {}

        for platform in platforms:
            try:
                adapted = await self._adapt_for_platform(
                    business_id, platform, title, body
                )
                results[platform] = adapted

                # Schedule in content calendar
                if adapted.get("content"):
                    entry = ContentCalendar(
                        business_id=business_id,
                        content_id=source_content_id,
                        platform=platform,
                        status="scheduled",
                        caption=adapted.get("caption", ""),
                    )
                    self.db.add(entry)
            except Exception as e:
                logger.error(f"Failed to syndicate to {platform}: {e}")
                results[platform] = {"error": str(e)}

        await self.db.commit()
        return {
            "source_id": str(source_content_id),
            "platforms": results,
            "platforms_scheduled": len([r for r in results.values() if "error" not in r]),
        }

    async def _adapt_for_platform(
        self,
        business_id: uuid.UUID,
        platform: str,
        title: str,
        body: str,
    ) -> dict:
        """Adapt content for a specific platform using AI."""
        adapters = {
            "instagram": self._adapt_instagram,
            "tiktok": self._adapt_tiktok,
            "linkedin": self._adapt_linkedin,
            "whatsapp_status": self._adapt_whatsapp_status,
            "email": self._adapt_email,
        }

        adapter = adapters.get(platform)
        if not adapter:
            return {"error": f"Unknown platform: {platform}"}

        return await adapter(business_id, title, body)

    async def _adapt_instagram(self, business_id: uuid.UUID, title: str, body: str) -> dict:
        """Adapt for Instagram: carousel script + caption + hashtags."""
        system_prompt = """Eres un experto en Instagram para negocios. Adaptas contenido a:
1. Carousels de 5-7 slides (cada slide: título corto + 1-2 oraciones)
2. Caption con hook + CTA
3. Hashtags estratégicos (3-5 nichos + 2-5 trending)

Responde en JSON:
{
  "carousel_slides": [{"slide": 1, "title": "...", "text": "..."}, ...],
  "caption": "Caption completo",
  "hashtags": ["#tag1", "#tag2", ...],
  "cta": "Call to action"
}"""

        user_prompt = f"Adapta este contenido para Instagram:\n\nTítulo: {title}\n\nContenido: {body[:800]}"

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1200,
                temperature=0.75,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Instagram adaptation failed: {e}")
            return self._fallback_instagram(title, body)

    async def _adapt_tiktok(self, business_id: uuid.UUID, title: str, body: str) -> dict:
        """Adapt for TikTok: hook + script + on-screen text."""
        system_prompt = """Eres un creador de TikTok viral. Adaptas contenido a:
1. Hook de 3 segundos (texto en pantalla)
2. Script de 30-60 segundos
3. On-screen text markers
4. Sonido sugerido
5. CTA para comentarios

Responde en JSON:
{
  "hook": "Texto que aparece en los primeros 3 segundos",
  "script": "Guion completo",
  "on_screen_text": ["0:03 Texto", "0:15 Texto"],
  "sound_suggestion": "Tipo de sonido",
  "cta": "CTA para comentarios"
}"""

        user_prompt = f"Adapta este contenido para TikTok:\n\nTítulo: {title}\n\nContenido: {body[:600]}"

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1000,
                temperature=0.8,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"TikTok adaptation failed: {e}")
            return self._fallback_tiktok(title, body)

    async def _adapt_linkedin(self, business_id: uuid.UUID, title: str, body: str) -> dict:
        """Adapt for LinkedIn: professional storytelling post."""
        system_prompt = """Eres un experto en LinkedIn personal branding. Adaptas contenido a posts que:
1. Usan storytelling profesional
2. Tienen estructura: Hook -> Story -> Lesson -> CTA
3. Incluyen bullets y espaciado
4. Terminan con pregunta de engagement
5. Usan 3-5 hashtags de nicho

Responde en JSON:
{
  "post": "Post completo formateado",
  "hashtags": ["#tag1", "#tag2"]
}"""

        user_prompt = f"Adapta este contenido para LinkedIn:\n\nTítulo: {title}\n\nContenido: {body[:1000]}"

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1200,
                temperature=0.7,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"LinkedIn adaptation failed: {e}")
            return self._fallback_linkedin(title, body)

    async def _adapt_whatsapp_status(self, business_id: uuid.UUID, title: str, body: str) -> dict:
        """Adapt for WhatsApp Status: short, punchy text."""
        system_prompt = """Eres un experto en WhatsApp Status para negocios. Creas textos de estado que:
1. Son cortos (máx 3 líneas)
2. Generan curiosidad
3. Incluyen CTA sutil (responder, deslizar arriba)
4. Usan emojis estratégicamente

Responde en JSON:
{
  "status_text": "Texto del estado",
  "cta": "Llamado a la acción"
}"""

        user_prompt = f"Adapta este contenido para WhatsApp Status:\n\nTítulo: {title}\n\nContenido: {body[:400]}"

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=400,
                temperature=0.75,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"WhatsApp Status adaptation failed: {e}")
            return self._fallback_whatsapp_status(title, body)

    async def _adapt_email(self, business_id: uuid.UUID, title: str, body: str) -> dict:
        """Adapt for Email newsletter format."""
        system_prompt = """Eres un email marketer experto. Adaptas contenido a newsletters que:
1. Tienen subject line con alta apertura
2. Preview text atractivo
3. Body scannable con headers y bullets
4. CTA claro
5. P.S. con gancho

Responde en JSON:
{
  "subject": "Subject line",
  "preview": "Preview text",
  "body": "Cuerpo del email",
  "cta": "Call to action",
  "ps": "P.S. line"
}"""

        user_prompt = f"Adapta este contenido para newsletter email:\n\nTítulo: {title}\n\nContenido: {body[:1000]}"

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1200,
                temperature=0.7,
            )
            import json
            return json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Email adaptation failed: {e}")
            return self._fallback_email(title, body)

    # ========== Fallbacks ==========

    def _fallback_instagram(self, title: str, body: str) -> dict:
        return {
            "carousel_slides": [
                {"slide": 1, "title": title, "text": "Descubre cómo..."},
                {"slide": 2, "title": "El problema", "text": body[:100]},
                {"slide": 3, "title": "La solución", "text": "Aquí va el tip principal"},
            ],
            "caption": f"{title}\n\n¿Te sirvió? Guardá este post para después 🔖",
            "hashtags": ["#emprendedores", "#negocios", "#marketing"],
            "cta": "Comentá SI si querés más tips",
        }

    def _fallback_tiktok(self, title: str, body: str) -> dict:
        return {
            "hook": f"NO hagas esto si querés {title.lower()}",
            "script": f"Mira, la mayoría de personas cometen este error... {body[:200]}",
            "on_screen_text": ["0:03 ERROR COMÚN", "0:15 LA SOLUCIÓN"],
            "sound_suggestion": "Trending motivational",
            "cta": "¿A vos te pasó? Contame en los comentarios",
        }

    def _fallback_linkedin(self, title: str, body: str) -> dict:
        return {
            "post": f"Hace 6 meses estaba frustrado con {title.lower()}.\n\nHoy quiero compartir lo que aprendí:\n\n• {body[:150]}\n• El cambio llega con consistencia\n• No necesitás más recursos, necesitás mejor enfoque\n\n¿Vos qué estrategia usás?\n\n#emprendedores #negocios",
            "hashtags": ["#emprendedores", "#negocios"],
        }

    def _fallback_whatsapp_status(self, title: str, body: str) -> dict:
        return {
            "status_text": f"💡 {title}\n\n{body[:120]}...",
            "cta": "Respondé para el tip completo 👆",
        }

    def _fallback_email(self, title: str, body: str) -> dict:
        return {
            "subject": f"[{title}] El tip que cambió todo",
            "preview": "Descubrí esto hace poco y tuve que compartirlo...",
            "body": f"<h1>{title}</h1><p>{body[:500]}</p>",
            "cta": "Quiero saber más",
            "ps": "P.S. Si te sirvió, respondé con un SI.",
        }
