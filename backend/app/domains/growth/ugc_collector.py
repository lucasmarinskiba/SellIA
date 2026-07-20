"""UGC Collector — User-Generated Content automation.

Requests, collects, and manages UGC from satisfied customers.
Reuses content in social posts and sales messages.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import UgcRequest, UgcRequestStatus, SocialProofItem, SocialProofType, SocialProofStatus
from app.domains.outreach.service import FatigueScoringService
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class UGCCollector:
    """Automated user-generated content collection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    # ========== Request ==========

    async def request_ugc(
        self,
        business_id: uuid.UUID,
        order_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content_type: str = "lifestyle_photo",  # unboxing, before_after, testimonial_video, lifestyle_photo, story
        incentive: str = "",
        campaign_id: uuid.UUID = None,
    ) -> UgcRequest:
        """Send a UGC request to a customer."""
        # Check if already requested for this order
        existing = await self.db.execute(
            select(UgcRequest).where(
                UgcRequest.order_id == order_id,
                UgcRequest.content_type == content_type,
            )
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one_or_none()

        # Generate personalized request
        message = await self._generate_ugc_request(
            business_id, content_type, incentive
        )

        ugc_request = UgcRequest(
            business_id=business_id,
            conversation_id=conversation_id,
            order_id=order_id,
            campaign_id=campaign_id,
            content_type=content_type,
            request_message=message,
            incentive_offered=incentive,
            status=UgcRequestStatus.PENDING,
        )
        self.db.add(ugc_request)
        await self.db.commit()
        await self.db.refresh(ugc_request)
        logger.info(f"Created UGC request {ugc_request.id} for order {order_id}")
        return ugc_request

    async def send_ugc_request(self, request_id: uuid.UUID) -> dict[str, Any]:
        """Send the UGC request message."""
        ugc_request = await self.db.get(UgcRequest, request_id)
        if not ugc_request:
            return {"status": "error", "reason": "not_found"}

        if ugc_request.status != UgcRequestStatus.PENDING:
            return {"status": "error", "reason": f"already_{ugc_request.status.value}"}

        # Check fatigue
        can_contact = await self.fatigue.can_contact_now(
            ugc_request.business_id, ugc_request.conversation_id
        )
        if not can_contact.get("allowed", True):
            return {"status": "blocked", "reason": "fatigue"}

        # Send message
        from app.domains.channels.services import send_outbound_message
        try:
            await send_outbound_message(
                self.db,
                ugc_request.conversation_id,
                ugc_request.request_message,
                content_type="text",
            )
        except Exception as e:
            logger.error(f"Failed to send UGC request: {e}")
            return {"status": "error", "reason": str(e)}

        ugc_request.status = UgcRequestStatus.SENT
        ugc_request.sent_at = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info(f"Sent UGC request {request_id} to conversation {ugc_request.conversation_id}")
        return {"status": "sent"}

    async def _generate_ugc_request(
        self,
        business_id: uuid.UUID,
        content_type: str,
        incentive: str,
    ) -> str:
        """Generate a personalized UGC request message."""
        type_descriptions = {
            "unboxing": "un video o foto desempaquetando tu producto",
            "before_after": "una foto de antes y después usando nuestro producto/servicio",
            "testimonial_video": "un video corto contando tu experiencia (30-60 segundos)",
            "lifestyle_photo": "una foto usando/disfrutando el producto en tu día a día",
            "story": "una story de Instagram mostrando tu experiencia",
        }

        system_prompt = """Eres un experto en solicitud de UGC (contenido generado por usuarios). Escribes mensajes que:
1. Hacen que los clientes QUIERAN compartir su experiencia
2. Dan instrucciones claras y simples
3. Agradecen sinceramente
4. NO suenan corporativos ni robóticos

Tono: amigo pidiendo un favor a otro amigo."""

        user_prompt = f"""Escribe un mensaje para pedirle a un cliente que comparta {type_descriptions.get(content_type, "una foto o video de su experiencia")}.

Incentivo: {incentive or "Serás destacado en nuestras redes y recibirás un agradecimiento especial"}

El mensaje debe:
- Agradecer la compra/experiencia primero
- Pedir el contenido de forma natural y entusiasta
- Dar instrucciones SIMPLES (máx 2 pasos)
- Mencionar el incentivo
- Ser máximo 100 palabras
- Sonar como un mensaje de amigo, no de empresa

Ejemplo para lifestyle photo:
"¡Ey! Me alegra un montón que estés disfrutando [producto]. ¿Te animás a sacar una foto usándolo en tu día a día? Me encantaría compartirla. Simplemente respondé con la foto y te muestro el agradecimiento especial que tengo para vos. ¡Gracias! 📸"""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=500,
                temperature=0.75,
            ) or f"¡Hola! Me encantaría ver tu experiencia con nuestro producto. ¿Podrías compartir una foto? Te lo agradezco mucho."
        except Exception as e:
            logger.error(f"Failed to generate UGC request: {e}")
            return f"¡Hola! Me encantaría ver tu experiencia con nuestro producto. ¿Podrías compartir una foto? Te lo agradezco mucho."

    # ========== Collection ==========

    async def collect_submission(
        self,
        request_id: uuid.UUID,
        media_urls: List[str],
        response_text: str = "",
    ) -> UgcRequest:
        """Record a UGC submission from a customer."""
        ugc_request = await self.db.get(UgcRequest, request_id)
        if not ugc_request:
            raise ValueError(f"UGC request {request_id} not found")

        ugc_request.status = UgcRequestStatus.RECEIVED
        ugc_request.response_media_urls = media_urls
        ugc_request.response_text = response_text
        ugc_request.responded_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(ugc_request)

        # Create social proof item from UGC
        if media_urls:
            proof_type = SocialProofType.UGC_VIDEO if any(url.endswith(('.mp4', '.mov')) for url in media_urls) else SocialProofType.UGC_PHOTO
            social_proof = SocialProofItem(
                business_id=ugc_request.business_id,
                conversation_id=ugc_request.conversation_id,
                order_id=ugc_request.order_id,
                item_type=proof_type,
                status=SocialProofStatus.PENDING,
                content=response_text or "Contenido generado por usuario",
                media_urls=media_urls,
            )
            self.db.add(social_proof)
            await self.db.commit()
            await self.db.refresh(social_proof)
            ugc_request.social_proof_id = social_proof.id
            await self.db.commit()

        # Emit event
        await event_bus.emit("ugc.submitted", {
            "business_id": str(ugc_request.business_id),
            "request_id": str(request_id),
            "media_count": len(media_urls),
        })

        logger.info(f"Collected UGC submission for request {request_id}")
        return ugc_request

    # ========== Campaigns ==========

    async def create_ugc_campaign(
        self,
        business_id: uuid.UUID,
        theme: str,
        content_type: str = "lifestyle_photo",
        incentive: str = "",
        campaign_id: uuid.UUID = None,
    ) -> dict[str, Any]:
        """Create a themed UGC challenge/campaign."""
        # Generate campaign message
        system_prompt = "Eres un experto en campañas de UGC. Creas desafíos que generan participación masiva."
        user_prompt = f"""Crea un desafío UGC con el tema: {theme}

Tipo de contenido: {content_type}
Incentivo: {incentive or "Destacado en redes sociales + agradecimiento especial"}

Responde en JSON:
{{
  "campaign_name": "Nombre atractivo del desafío",
  "hashtag": "#HashtagUnico",
  "description": "Descripción del desafío (máx 3 oraciones)",
  "instructions": "Instrucciones simples para participar",
  "cta": "Llamado a la acción claro"
}}"""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.8,
            )
            import json
            campaign_data = json.loads(response or "{}")
        except Exception as e:
            logger.error(f"Failed to generate UGC campaign: {e}")
            campaign_data = {
                "campaign_name": f"Desafío {theme}",
                "hashtag": f"#{theme.replace(' ', '')}",
                "description": f"Comparte tu experiencia con {theme}",
                "instructions": "1. Saca una foto/video. 2. Compártela respondiendo a este mensaje.",
                "cta": "¡Participa ahora!",
            }

        return {
            "business_id": str(business_id),
            "campaign_id": str(campaign_id) if campaign_id else None,
            **campaign_data,
        }

    # ========== Gallery ==========

    async def get_ugc_gallery(
        self,
        business_id: uuid.UUID,
        content_type: str = None,
        limit: int = 50,
    ) -> List[dict]:
        """Get approved UGC items for gallery display."""
        query = select(UgcRequest).where(
            UgcRequest.business_id == business_id,
            UgcRequest.status.in_([UgcRequestStatus.RECEIVED, UgcRequestStatus.APPROVED]),
        ).order_by(desc(UgcRequest.responded_at)).limit(limit)

        if content_type:
            query = query.where(UgcRequest.content_type == content_type)

        result = await self.db.execute(query)
        requests = result.scalars().all()

        gallery = []
        for req in requests:
            gallery.append({
                "id": str(req.id),
                "content_type": req.content_type,
                "media_urls": req.response_media_urls,
                "response_text": req.response_text,
                "status": req.status.value,
                "responded_at": req.responded_at.isoformat() if req.responded_at else None,
            })
        return gallery

    async def approve_ugc(self, request_id: uuid.UUID) -> UgcRequest:
        """Approve a UGC submission for reuse."""
        ugc_request = await self.db.get(UgcRequest, request_id)
        if not ugc_request:
            raise ValueError(f"UGC request {request_id} not found")

        ugc_request.status = UgcRequestStatus.APPROVED

        # Also approve linked social proof
        if ugc_request.social_proof_id:
            from app.domains.growth.social_proof import SocialProofEngine
            engine = SocialProofEngine(self.db)
            await engine.approve_item(ugc_request.social_proof_id)

        await self.db.commit()
        await self.db.refresh(ugc_request)
        return ugc_request

    async def get_pending_requests(self, business_id: uuid.UUID) -> List[UgcRequest]:
        """Get pending UGC requests that need to be sent."""
        result = await self.db.execute(
            select(UgcRequest).where(
                UgcRequest.business_id == business_id,
                UgcRequest.status == UgcRequestStatus.PENDING,
            ).order_by(UgcRequest.created_at)
        )
        return list(result.scalars().all())
