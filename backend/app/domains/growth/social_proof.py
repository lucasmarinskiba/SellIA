"""Social Proof Engine — Automated testimonial and review collection.

Collects, analyzes, moderates, and injects social proof into sales conversations.
Integrates with MessageIntelligenceService for sentiment analysis.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import SocialProofItem, SocialProofType, SocialProofStatus
from app.domains.intelligence.service import MessageIntelligenceService
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class SocialProofEngine:
    """Automated social proof collection and management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intelligence = MessageIntelligenceService(db)

    # ========== Collection ==========

    async def request_review(
        self,
        business_id: uuid.UUID,
        order_id: uuid.UUID,
        conversation_id: uuid.UUID,
        channel: str = "whatsapp",
        delay_hours: int = 72,
    ) -> dict[str, Any]:
        """Send a review request to a customer."""
        # Check if already requested
        existing = await self.db.execute(
            select(SocialProofItem).where(
                SocialProofItem.order_id == order_id,
                SocialProofItem.item_type.in_([SocialProofType.REVIEW, SocialProofType.RATING]),
            )
        )
        if existing.scalar_one_or_none():
            return {"status": "already_requested"}

        # Generate personalized request message
        message = await self._generate_review_request(business_id, channel)

        # Send message (immediate or scheduled)
        if delay_hours <= 0:
            from app.domains.channels.services import send_outbound_message
            try:
                await send_outbound_message(
                    self.db,
                    conversation_id,
                    message,
                    content_type="text",
                )
            except Exception as e:
                logger.error(f"Failed to send review request: {e}")
                return {"status": "error", "reason": str(e)}

        logger.info(f"Sent review request for order {order_id} to conversation {conversation_id}")
        return {"status": "sent", "channel": channel, "delay_hours": delay_hours}

    async def _generate_review_request(self, business_id: uuid.UUID, channel: str) -> str:
        """Generate a personalized review request message."""
        system_prompt = """Eres un experto en solicitud de reviews. Escribes mensajes que:
1. Suenan genuinos y personales
2. Hacen que dejar una review sea fácil
3. NO suenan desesperados ni agresivos
4. Agradecen sinceramente al cliente

Tono: agradecido, casual, sin presión."""

        user_prompt = f"""Escribe un mensaje corto para pedir una review/testimonial a un cliente satisfecho.

Canal: {channel}

El mensaje debe:
- Agradecer la compra/experiencia
- Pedir la review de forma natural
- Sugerir qué podría mencionar (resultados, experiencia, recomendación)
- Incluir un CTA fácil (responder con estrellas 1-5 + comentario)
- Ser máximo 80 palabras
- NO ofrecer incentivos (eso reduce credibilidad)

Ejemplo: "¡Hola! Espero que estés disfrutando [producto]. Me ayudaría MUCHO si me contás cómo fue tu experiencia. Simplemente respondé con ⭐ (1-5) y una frase. ¡Gracias de corazón!"""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=400,
                temperature=0.7,
            ) or "¡Hola! Espero que estés disfrutando tu compra. Me ayudaría MUCHO si me contás cómo fue tu experiencia. Simplemente respondé con ⭐ (1-5) y una frase. ¡Gracias de corazón!"
        except Exception as e:
            logger.error(f"Failed to generate review request: {e}")
            return "¡Hola! Espero que estés disfrutando tu compra. Me ayudaría MUCHO si me contás cómo fue tu experiencia. Simplemente respondé con ⭐ (1-5) y una frase. ¡Gracias de corazón!"

    async def collect_testimonial(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content: str,
        order_id: uuid.UUID = None,
        customer_name: str = None,
        media_urls: List[str] = None,
    ) -> SocialProofItem:
        """Collect and analyze a customer testimonial/review."""
        # Analyze sentiment
        sentiment_score = await self._analyze_sentiment(content)

        # Auto-approve if highly positive
        status = SocialProofStatus.AUTO_APPROVED if sentiment_score > 0.7 else SocialProofStatus.PENDING

        # Generate AI summary
        ai_summary = await self._generate_summary(business_id, content)

        # Extract key quotes
        key_quotes = await self._extract_quotes(business_id, content)

        item = SocialProofItem(
            business_id=business_id,
            conversation_id=conversation_id,
            order_id=order_id,
            item_type=SocialProofType.TESTIMONIAL,
            status=status,
            content=content,
            customer_name=customer_name,
            media_urls=media_urls or [],
            sentiment_score=sentiment_score,
            ai_summary=ai_summary,
            key_quotes=key_quotes,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        # Emit event
        await event_bus.emit("social_proof.collected", {
            "business_id": str(business_id),
            "item_id": str(item.id),
            "type": "testimonial",
            "sentiment_score": float(sentiment_score),
            "auto_approved": status == SocialProofStatus.AUTO_APPROVED,
        })

        if status == SocialProofStatus.AUTO_APPROVED:
            await event_bus.emit("social_proof.approved", {
                "business_id": str(business_id),
                "item_id": str(item.id),
            })

        logger.info(f"Collected social proof item {item.id} (sentiment: {sentiment_score})")
        return item

    async def _analyze_sentiment(self, content: str) -> float:
        """Analyze sentiment of a review/testimonial."""
        # Simple heuristic: count positive vs negative words
        positive_words = ["excelente", "genial", "increíble", "fantástico", "amazing", "great", "love", "perfecto", "recomiendo", "mejor", "buenísimo", "súper", "encantado", "satisfecho", "feliz", "gracias", "maravilloso", "outstanding", "awesome"]
        negative_words = ["malo", "horrible", "terrible", "peor", "decepcionado", "problema", "error", "falla", "lento", "caro", "fraude", "estafa", "malo", "defectuoso", "worst", "hate", "disappointed", "bad", "poor"]

        content_lower = content.lower()
        pos_count = sum(1 for word in positive_words if word in content_lower)
        neg_count = sum(1 for word in negative_words if word in content_lower)
        total = pos_count + neg_count

        if total == 0:
            return 0.0
        return (pos_count - neg_count) / max(total, 3)

    async def _generate_summary(self, business_id: uuid.UUID, content: str) -> str:
        """Generate AI summary of testimonial."""
        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt="Resume testimonios en 1-2 oraciones capturando el beneficio principal.",
                user_prompt=f"Resume este testimonio: {content[:500]}",
                max_tokens=150,
                temperature=0.5,
            ) or ""
        except Exception:
            return ""

    async def _extract_quotes(self, business_id: uuid.UUID, content: str) -> List[str]:
        """Extract powerful quotes from testimonial."""
        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt='Extrae 1-2 frases cortas y poderosas de testimonios. Responde en JSON: {"quotes": ["...", "..."]}.',
                user_prompt=f"Extrae las frases más impactantes de: {content[:500]}",
                max_tokens=200,
                temperature=0.5,
            )
            import json
            parsed = json.loads(response or "{}")
            return parsed.get("quotes", [])
        except Exception:
            return []

    # ========== Moderation ==========

    async def approve_item(self, item_id: uuid.UUID, approved_by: uuid.UUID = None) -> SocialProofItem:
        """Manually approve a social proof item."""
        item = await self.db.get(SocialProofItem, item_id)
        if not item:
            raise ValueError(f"Social proof item {item_id} not found")

        item.status = SocialProofStatus.APPROVED
        item.approved_by = approved_by
        item.approved_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)

        await event_bus.emit("social_proof.approved", {
            "business_id": str(item.business_id),
            "item_id": str(item_id),
        })

        return item

    async def reject_item(self, item_id: uuid.UUID, reason: str = "") -> SocialProofItem:
        """Reject a social proof item."""
        item = await self.db.get(SocialProofItem, item_id)
        if not item:
            raise ValueError(f"Social proof item {item_id} not found")

        item.status = SocialProofStatus.REJECTED
        item.rejection_reason = reason
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ========== Retrieval & Injection ==========

    async def get_social_proof_wall(
        self,
        business_id: uuid.UUID,
        item_type: SocialProofType = None,
        count: int = 10,
        min_rating: int = None,
    ) -> List[SocialProofItem]:
        """Get approved social proof items for display."""
        query = select(SocialProofItem).where(
            SocialProofItem.business_id == business_id,
            SocialProofItem.status.in_([SocialProofStatus.APPROVED, SocialProofStatus.AUTO_APPROVED]),
            SocialProofItem.is_active == True,
        )
        if item_type:
            query = query.where(SocialProofItem.item_type == item_type)
        if min_rating:
            query = query.where(SocialProofItem.rating >= min_rating)
        query = query.order_by(desc(SocialProofItem.sentiment_score)).limit(count)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def inject_into_message(
        self,
        business_id: uuid.UUID,
        message: str,
        item_type: SocialProofType = SocialProofType.TESTIMONIAL,
    ) -> str:
        """Add relevant social proof to a sales message."""
        items = await self.get_social_proof_wall(business_id, item_type=item_type, count=1)
        if not items:
            return message

        item = items[0]
        item.usage_count += 1
        item.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Format testimonial snippet
        testimonial_snippet = f'"{item.content[:120]}..." — {item.customer_name or "Cliente feliz"}'
        social_proof_block = f"\n\n💬 {testimonial_snippet}\n"

        return message + social_proof_block

    async def get_moderation_queue(self, business_id: uuid.UUID) -> List[SocialProofItem]:
        """Get pending social proof items for moderation."""
        result = await self.db.execute(
            select(SocialProofItem).where(
                SocialProofItem.business_id == business_id,
                SocialProofItem.status == SocialProofStatus.PENDING,
            ).order_by(desc(SocialProofItem.created_at))
        )
        return list(result.scalars().all())

    async def get_stats(self, business_id: uuid.UUID) -> dict[str, Any]:
        """Get social proof statistics."""
        total_result = await self.db.execute(
            select(func.count(SocialProofItem.id)).where(
                SocialProofItem.business_id == business_id,
            )
        )
        total = total_result.scalar() or 0

        approved_result = await self.db.execute(
            select(func.count(SocialProofItem.id)).where(
                SocialProofItem.business_id == business_id,
                SocialProofItem.status.in_([SocialProofStatus.APPROVED, SocialProofStatus.AUTO_APPROVED]),
            )
        )
        approved = approved_result.scalar() or 0

        avg_sentiment_result = await self.db.execute(
            select(func.avg(SocialProofItem.sentiment_score)).where(
                SocialProofItem.business_id == business_id,
            )
        )
        avg_sentiment = avg_sentiment_result.scalar() or 0

        return {
            "total_collected": total,
            "approved": approved,
            "pending": total - approved,
            "approval_rate": round((approved / total * 100), 2) if total > 0 else 0,
            "average_sentiment": round(float(avg_sentiment), 3),
        }
