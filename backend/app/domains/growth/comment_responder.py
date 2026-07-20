"""Auto-Comment Responder — Engages with social comments automatically.

Monitors social media comments and auto-responds with value,
moving interested users from public comments to private DMs.
This is one of the highest-ROI organic growth strategies.
"""

import uuid
import re
from typing import Optional, Any, List, Dict
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.outreach.service import FatigueScoringService
from app.domains.growth.models import InboundLead, InboundLeadSource
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)

# Keywords that indicate high intent in comments
HIGH_INTENT_KEYWORDS = [
    "precio", "precios", "cuanto", "cuánto", "costo", "valor",
    "como compro", "como comprar", "donde", "dónde", "link",
    "quiero", "me interesa", "info", "información", "informacion",
    "disponible", "stock", "envian", "envían", "a domicilio",
    "price", "how much", "cost", "buy", "interested", "link",
    "dm", "mensaje", "whatsapp", "consulta",
]

# Value-first response keywords (educational engagement)
VALUE_KEYWORDS = [
    "consejo", "tip", "ayuda", "como hago", "cómo hago",
    "tutorial", "guía", "guia", "explica", "explicá",
    "tips", "consejos", "ayudame", "ayúdame",
    "help", "how to", "tips", "advice", "explain",
]


class CommentResponder:
    """Auto-responds to social media comments with value + DM bridge."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    async def process_comment(
        self,
        business_id: uuid.UUID,
        platform: str,
        post_id: str,
        comment_id: str,
        author_username: str,
        comment_text: str,
        author_id: str = None,
    ) -> dict[str, Any]:
        """Process a single comment and generate response strategy."""
        comment_lower = comment_text.lower()

        # Analyze intent
        has_high_intent = any(kw in comment_lower for kw in HIGH_INTENT_KEYWORDS)
        has_value_request = any(kw in comment_lower for kw in VALUE_KEYWORDS)
        is_generic = len(comment_text.strip()) < 5

        if is_generic:
            return {"action": "skip", "reason": "too_short"}

        # Determine response strategy
        if has_high_intent:
            return await self._handle_high_intent_comment(
                business_id, platform, author_username, comment_text, post_id
            )
        elif has_value_request:
            return await self._handle_value_comment(
                business_id, platform, author_username, comment_text, post_id
            )
        else:
            return await self._handle_engagement_comment(
                business_id, platform, author_username, comment_text, post_id
            )

    async def _handle_high_intent_comment(
        self,
        business_id: uuid.UUID,
        platform: str,
        author_username: str,
        comment_text: str,
        post_id: str,
    ) -> dict[str, Any]:
        """Handle comment with buying intent — reply publicly + DM immediately."""
        # Generate public reply (brief, with DM bridge)
        public_reply = await self._generate_public_reply(
            business_id, comment_text, "high_intent"
        )

        # Generate DM message
        dm_message = await self._generate_dm_message(
            business_id, author_username, "high_intent"
        )

        # Capture as inbound lead
        lead = await self._capture_comment_lead(
            business_id, platform, author_username, post_id, "high_intent"
        )

        logger.info(f"High-intent comment from @{author_username} on {platform}")

        return {
            "action": "reply_and_dm",
            "public_reply": public_reply,
            "dm_message": dm_message,
            "lead_id": str(lead.id) if lead else None,
            "priority": "high",
        }

    async def _handle_value_comment(
        self,
        business_id: uuid.UUID,
        platform: str,
        author_username: str,
        comment_text: str,
        post_id: str,
    ) -> dict[str, Any]:
        """Handle comment asking for tips/advice — give value + soft DM bridge."""
        # Give mini value bomb in public reply
        public_reply = await self._generate_public_reply(
            business_id, comment_text, "value_request"
        )

        # DM with expanded value
        dm_message = await self._generate_dm_message(
            business_id, author_username, "value_expansion"
        )

        lead = await self._capture_comment_lead(
            business_id, platform, author_username, post_id, "value_lead"
        )

        return {
            "action": "value_reply_and_dm",
            "public_reply": public_reply,
            "dm_message": dm_message,
            "lead_id": str(lead.id) if lead else None,
            "priority": "medium",
        }

    async def _handle_engagement_comment(
        self,
        business_id: uuid.UUID,
        platform: str,
        author_username: str,
        comment_text: str,
        post_id: str,
    ) -> dict[str, Any]:
        """Handle generic engagement comment — reply warmly, no DM."""
        public_reply = await self._generate_public_reply(
            business_id, comment_text, "engagement"
        )

        return {
            "action": "reply_only",
            "public_reply": public_reply,
            "priority": "low",
        }

    async def _generate_public_reply(
        self,
        business_id: uuid.UUID,
        comment_text: str,
        intent_type: str,
    ) -> str:
        """Generate a public comment reply."""
        system_prompt = f"""Eres un community manager que responde comentarios en redes sociales.
Tipo de respuesta: {intent_type}
- high_intent: Responder con entusiasmo + decir que les mandaste DM
- value_request: Dar un mini tip valioso (1-2 oraciones) + decir que les mandaste más por DM
- engagement: Responder con gratitud y calidez

Reglas:
- Máximo 25 palabras
- Emojis naturales
- NUNCA vender en público
- Siempre sonar humano"""

        user_prompt = f"Comentario del usuario: \"{comment_text}\"\n\nResponde en UNA oración corta."

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=150,
                temperature=0.8,
            ) or "¡Gracias por tu comentario! Te mandé un DM con más info 💬"
        except Exception as e:
            logger.error(f"Public reply generation failed: {e}")
            return "¡Gracias por tu comentario! Te mandé un DM con más info 💬"

    async def _generate_dm_message(
        self,
        business_id: uuid.UUID,
        username: str,
        dm_type: str,
    ) -> str:
        """Generate a DM message for comment responders."""
        system_prompt = f"""Eres un emprendedor que responde DMs de personas que comentaron en sus posts.
Tipo: {dm_type}
- high_intent: Ir directo al punto, ofrecer ayuda con su consulta
- value_expansion: Dar el tip completo que prometiste en el comentario

Reglas:
- Personalizar con @{username}
- Máximo 80 palabras
- Tono: cálido, no robótico
- NO spam
- Pregunta de descubrimiento al final"""

        user_prompt = f"Escribe un DM para @{username} que comentó en tu post."

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8,
            ) or f"Hola @{username}! Ví tu comentario y quería ayudarte con eso. ¿En qué andás ahora?"
        except Exception as e:
            logger.error(f"DM generation failed: {e}")
            return f"Hola @{username}! Ví tu comentario y quería ayudarte con eso. ¿En qué andás ahora?"

    async def _capture_comment_lead(
        self,
        business_id: uuid.UUID,
        platform: str,
        username: str,
        post_id: str,
        source_detail: str,
    ) -> Optional[InboundLead]:
        """Capture a lead from social comment."""
        lead = InboundLead(
            business_id=business_id,
            source_type=InboundLeadSource.COMMENT_DM,
            source_detail=f"{platform}_post:{post_id}_comment_by:{username}",
            contact_info={"username": username, "platform": platform},
        )
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)

        await event_bus.emit("inbound.lead_captured", {
            "business_id": str(business_id),
            "lead_id": str(lead.id),
            "source_type": "comment_dm",
        })

        return lead

    async def get_comment_analytics(
        self,
        business_id: uuid.UUID,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get analytics on comment engagement."""
        since = datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days)

        result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.source_type == InboundLeadSource.COMMENT_DM,
                InboundLead.first_touch_at >= since,
            )
        )
        comment_leads = result.scalar() or 0

        return {
            "period_days": days,
            "leads_from_comments": comment_leads,
            "avg_response_time_seconds": 120,  # Target: respond in < 2 min
            "engagement_rate": "placeholder",
        }
