"""Lead Magnet Funnel Engine — Automated lead magnet creation, delivery, and tracking.

Generates irresistible lead magnets using AI, sets up auto-delivery workflows,
and tracks conversion rates end-to-end.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import LeadMagnet, LeadMagnetFormat, InboundLead, InboundLeadSource
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.outreach.service import FatigueScoringService
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class LeadMagnetEngine:
    """End-to-end lead magnet automation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    # ========== Generation ==========

    async def generate_lead_magnet(
        self,
        business_id: uuid.UUID,
        topic: str,
        magnet_format: LeadMagnetFormat = LeadMagnetFormat.CHEAT_SHEET,
        target_audience: str = "",
        campaign_id: uuid.UUID = None,
    ) -> LeadMagnet:
        """Generate a complete lead magnet with AI."""
        # Generate content
        content = await self._generate_content(business_id, topic, magnet_format, target_audience)
        landing_copy = await self._generate_landing_copy(business_id, topic, content)
        delivery_msg = await self._generate_delivery_message(business_id, topic, magnet_format)

        magnet = LeadMagnet(
            business_id=business_id,
            campaign_id=campaign_id,
            title=content.get("title", f"Guía gratuita: {topic}"),
            description=content.get("description", ""),
            format=magnet_format,
            topic=topic,
            content={
                "sections": content.get("sections", []),
                "key_takeaways": content.get("key_takeaways", []),
                "preview_text": content.get("preview_text", ""),
            },
            landing_page_copy=landing_copy,
            delivery_message=delivery_msg,
            call_to_action=content.get("cta", "Descarga gratis ahora"),
            auto_deliver=True,
            delivery_channel="whatsapp",
            delivery_trigger="new_lead",
        )
        self.db.add(magnet)
        await self.db.commit()
        await self.db.refresh(magnet)
        logger.info(f"Generated lead magnet {magnet.id} ({magnet_format.value}) for business {business_id}")
        return magnet

    async def _generate_content(
        self,
        business_id: uuid.UUID,
        topic: str,
        magnet_format: LeadMagnetFormat,
        target_audience: str,
    ) -> dict[str, Any]:
        """Use AI to generate lead magnet content."""
        format_names = {
            LeadMagnetFormat.CHEAT_SHEET: "hoja de referencia rápida (cheat sheet)",
            LeadMagnetFormat.TEMPLATE: "plantilla descargable",
            LeadMagnetFormat.CALCULATOR: "calculadora interactiva",
            LeadMagnetFormat.MINI_GUIDE: "mini guía PDF",
            LeadMagnetFormat.QUIZ: "cuestionario de autodiagnóstico",
            LeadMagnetFormat.AUDIT: "checklist de auditoría",
            LeadMagnetFormat.TOOLKIT: "kit de herramientas",
            LeadMagnetFormat.CHECKLIST: "lista de verificación",
            LeadMagnetFormat.EBOOK: "ebook corto",
            LeadMagnetFormat.VIDEO_MINI: "video tutorial corto",
        }

        system_prompt = f"""Eres el Lead Magnet Architect AI. Creas lead magnets irresistibles que convierten extraños en prospectos cualificados.

Tu especialidad:
1. Identificas EL micro-problema doloroso del cliente ideal
2. Creas lead magnets en formato: {format_names.get(magnet_format, "guía")}
3. Nombras usando la fórmula M.A.G.I.C. (Magnetic, Actionable, Generous, Instant, Concrete)
4. Diseñas el "value gap" — el lead magnet resuelve un problema pequeño mientras hace obvio el problema grande

Responde ÚNICAMENTE en JSON válido con esta estructura:
{{
  "title": "Título atractivo del lead magnet",
  "description": "Descripción de 2-3 oraciones",
  "sections": ["Sección 1", "Sección 2", "Sección 3"],
  "key_takeaways": ["Insight 1", "Insight 2", "Insight 3"],
  "preview_text": "Texto de preview para mostrar antes de descargar",
  "cta": "Llamado a la acción claro"
}}"""

        user_prompt = f"""Crea un lead magnet sobre: {topic}

Público objetivo: {target_audience or "emprendedores y dueños de negocios"}

El lead magnet debe:
- Resolver un problema específico en 5-10 minutos de lectura/uso
- Dejar al usuario queriendo más (el problema grande)
- Ser altamente actionable (no teórico)
- Tener un título que genere curiosidad + promesa clara"""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.8,
            )
            import json
            parsed = json.loads(response or "{}")
            return parsed
        except Exception as e:
            logger.error(f"Failed to generate lead magnet content: {e}")
            return {
                "title": f"Guía gratuita: {topic}",
                "description": f"Descubre cómo resolver {topic} con esta guía práctica.",
                "sections": ["Introducción", "Los 5 pasos clave", "Checklist de acción"],
                "key_takeaways": ["Aprende la estrategia paso a paso", "Evita errores comunes", "Aplica inmediatamente"],
                "preview_text": f"En esta guía descubrirás los secretos para dominar {topic}.",
                "cta": "Descarga gratis ahora",
            }

    async def _generate_landing_copy(self, business_id: uuid.UUID, topic: str, content: dict) -> str:
        """Generate conversion-optimized landing page copy."""
        system_prompt = "Eres un copywriter experto en landing pages. Escribes copy que convierte visitantes en leads."
        user_prompt = f"""Escribe el copy de una landing page para un lead magnet gratuito sobre: {topic}

Título del lead magnet: {content.get('title', topic)}
Descripción: {content.get('description', '')}

Incluye:
1. Headline principal (hook emocional + promesa)
2. Subheadline (credibilidad + contexto)
3. 3 bullets de beneficio
4. Formulario simple (nombre + email/WhatsApp)
5. CTA button copy

Máximo 200 palabras. Tono: conversacional, urgencia suave, sin ser agresivo."""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.7,
            ) or ""
        except Exception as e:
            logger.error(f"Failed to generate landing copy: {e}")
            return ""

    async def _generate_delivery_message(self, business_id: uuid.UUID, topic: str, magnet_format: LeadMagnetFormat) -> str:
        """Generate the auto-delivery DM message."""
        system_prompt = "Eres un experto en mensajes de WhatsApp/Instagram DM. Escribes mensajes cortos, personales, que generan valor inmediato."
        user_prompt = f"""Escribe un mensaje de DM para entregar un lead magnet gratuito sobre: {topic}

El mensaje debe:
- Ser personal y cálido (máx 80 palabras)
- Agradecer el interés
- Entregar el recurso con entusiasmo
- Incluir una pregunta de descubrimiento SUAVE al final
- NO sonar robótico o spam

Ejemplo de tono: "¡Hola [nombre]! Aquí tienes la guía que pediste. Espero que te sea super útil. Cuéntame: ¿cuál es el mayor desafío que estás enfrentando con [tema] ahora mismo?"
"""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=400,
                temperature=0.7,
            ) or ""
        except Exception as e:
            logger.error(f"Failed to generate delivery message: {e}")
            return f"¡Hola! Aquí tienes la guía sobre {topic} que solicitaste. Espero que te sea de gran ayuda."

    # ========== Delivery ==========

    async def deliver_lead_magnet(
        self,
        magnet_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Deliver a lead magnet to a conversation."""
        magnet = await self._get_magnet(magnet_id)
        if not magnet:
            return {"error": "Lead magnet not found"}

        # Check fatigue
        can_contact = await self.fatigue.can_contact_now(
            magnet.business_id, conversation_id, channel=magnet.delivery_channel
        )
        if not can_contact.get("allowed", True):
            logger.info(f"Fatigue blocked lead magnet delivery to {conversation_id}")
            return {"status": "blocked", "reason": can_contact.get("reason", "fatigue")}

        # Send message
        from app.domains.channels.services import send_outbound_message
        message_text = magnet.delivery_message or f"¡Hola! Aquí tienes: {magnet.title}"

        try:
            await send_outbound_message(
                self.db,
                conversation_id,
                message_text,
                content_type="text",
            )
        except Exception as e:
            logger.error(f"Failed to send lead magnet message: {e}")
            return {"status": "error", "reason": str(e)}

        # Update metrics
        magnet.times_delivered += 1
        await self.db.commit()

        # Emit event
        await event_bus.emit("lead_magnet.delivered", {
            "business_id": str(magnet.business_id),
            "magnet_id": str(magnet_id),
            "conversation_id": str(conversation_id),
        })

        logger.info(f"Delivered lead magnet {magnet_id} to conversation {conversation_id}")
        return {"status": "delivered", "magnet_id": str(magnet_id)}

    async def track_conversion(
        self,
        magnet_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> LeadMagnet:
        """Track when a lead magnet recipient converts."""
        magnet = await self._get_magnet(magnet_id)
        if not magnet:
            raise ValueError(f"Lead magnet {magnet_id} not found")

        magnet.times_converted += 1
        if magnet.times_delivered > 0:
            magnet.conversion_rate = (magnet.times_converted / magnet.times_delivered) * 100

        await self.db.commit()
        await self.db.refresh(magnet)

        # Emit event
        await event_bus.emit("lead_magnet.converted", {
            "business_id": str(magnet.business_id),
            "magnet_id": str(magnet_id),
            "conversation_id": str(conversation_id),
        })

        return magnet

    # ========== Performance ==========

    async def get_performance_report(self, magnet_id: uuid.UUID) -> dict[str, Any]:
        """Get detailed performance report for a lead magnet."""
        magnet = await self._get_magnet(magnet_id)
        if not magnet:
            return {"error": "Lead magnet not found"}

        return {
            "magnet_id": str(magnet_id),
            "title": magnet.title,
            "format": magnet.format.value,
            "times_delivered": magnet.times_delivered,
            "times_downloaded": magnet.times_downloaded,
            "times_converted": magnet.times_converted,
            "conversion_rate": float(magnet.conversion_rate or 0),
            "engagement_score": float(magnet.engagement_score or 0),
            "is_active": magnet.is_active,
        }

    async def get_top_performing_magnets(self, business_id: uuid.UUID, limit: int = 5) -> list:
        """Get top performing lead magnets by conversion rate."""
        result = await self.db.execute(
            select(LeadMagnet).where(
                LeadMagnet.business_id == business_id,
                LeadMagnet.is_active == True,
            ).order_by(desc(LeadMagnet.conversion_rate)).limit(limit)
        )
        magnets = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "title": m.title,
                "format": m.format.value,
                "conversion_rate": float(m.conversion_rate or 0),
                "times_delivered": m.times_delivered,
            }
            for m in magnets
        ]

    # ========== Helpers ==========

    async def _get_magnet(self, magnet_id: uuid.UUID) -> Optional[LeadMagnet]:
        result = await self.db.execute(
            select(LeadMagnet).where(LeadMagnet.id == magnet_id)
        )
        return result.scalar_one_or_none()
