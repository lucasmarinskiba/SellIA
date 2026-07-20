"""Value-First Outreach Engine — Educational nurturing without sales pressure.

Implements the Jab-Jab-Jab-Right-Hook philosophy: 3 pure value touches
before any sales ask. Warms up cold leads through education.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import (
    ValueSequence, ValueSequenceEnrollment,
    InboundLead, NurturingStage,
)
from app.domains.outreach.service import FatigueScoringService
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class ValueFirstOutreach:
    """Pure-value educational nurturing sequences."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    # ========== Sequence Creation ==========

    async def create_educational_sequence(
        self,
        business_id: uuid.UUID,
        name: str,
        topic: str,
        message_count: int = 3,
        total_duration_days: int = 7,
        target_segment: str = "cold",
        campaign_id: uuid.UUID = None,
    ) -> ValueSequence:
        """Create an AI-generated educational value sequence."""
        messages = await self._generate_sequence_messages(
            business_id, topic, message_count, total_duration_days
        )

        sequence = ValueSequence(
            business_id=business_id,
            campaign_id=campaign_id,
            name=name,
            topic=topic,
            messages=messages,
            message_count=message_count,
            total_duration_days=total_duration_days,
            target_segment=target_segment,
        )
        self.db.add(sequence)
        await self.db.commit()
        await self.db.refresh(sequence)
        logger.info(f"Created value sequence {sequence.id} ({message_count} messages) for business {business_id}")
        return sequence

    async def _generate_sequence_messages(
        self,
        business_id: uuid.UUID,
        topic: str,
        message_count: int,
        total_duration_days: int,
    ) -> List[dict]:
        """Generate AI-powered educational messages."""
        avg_delay = (total_duration_days * 24) // message_count

        system_prompt = f"""Eres un experto en nurturing educativo. Creas secuencias de mensajes que:
1. ENTREGAN VALOR PURO sin pedir nada a cambio (Jab-Jab-Jab)
2. Educar al lead sobre un tema específico
3. Generan confianza y posicionan al negocio como experto
4. El último mensaje puede tener un CTA SUAVE (Right Hook)

Reglas:
- Cada mensaje debe ser útil por sí solo
- NO mencionar precios ni productos en los primeros {message_count - 1} mensajes
- El mensaje final puede ofrecer una llamada/demostración SIN PRESIÓN
- Tono: mentor amigable, experto accesible
- Máximo 150 palabras por mensaje
- Incluye un insight o tip práctico en cada mensaje

Responde en JSON:
{{
  "messages": [
    {{"order": 1, "subject": "Asunto/email subject", "content": "Mensaje completo", "delay_hours": {avg_delay}, "type": "value", "tip": "El tip práctico incluido"}},
    ...
  ]
}}"""

        user_prompt = f"""Crea una secuencia de {message_count} mensajes educativos sobre: {topic}

Duración total: {total_duration_days} días

Estructura:
- Mensaje 1: Bienvenida + insight sorprendente (hook educativo)
- Mensaje 2: Tip práctico que puedan aplicar hoy
- {"Mensaje 3: Caso de estudio o ejemplo real" if message_count >= 3 else ""}
- {"Mensaje 4: Deep dive en una técnica avanzada" if message_count >= 4 else ""}
- Mensaje {message_count}: CTA suave para una llamada/demostración (sin presión)

Cada mensaje debe hacer que el lead piense: "wow, esto es útil, quiero más de esta persona."

NO uses frases genéricas como "espero que estés bien". Sé directo y valioso."""

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2500,
                temperature=0.75,
            )
            import json
            parsed = json.loads(response or "{}")
            return parsed.get("messages", [])
        except Exception as e:
            logger.error(f"Failed to generate sequence messages: {e}")
            return self._fallback_messages(topic, message_count, avg_delay)

    def _fallback_messages(self, topic: str, count: int, delay_hours: int) -> List[dict]:
        """Fallback messages if AI generation fails."""
        messages = [
            {
                "order": 1,
                "subject": f"El secreto que nadie te cuenta sobre {topic}",
                "content": f"Hola! Quería compartirte algo que descubrí sobre {topic}. La mayoría de personas cometen este error: intentan todo a la vez en lugar de enfocarse en una estrategia. El tip de hoy: elige UNA táctica, domínala, y luego amplía. ¿Cuál es la táctica que más te cuesta dominar? Me encantaría saber.",
                "delay_hours": delay_hours,
                "type": "value",
                "tip": "Enfócate en una táctica a la vez",
            },
            {
                "order": 2,
                "subject": f"Tip práctico: cómo mejorar tu {topic} hoy mismo",
                "content": f"Aquí va un tip que puedes aplicar en los próximos 30 minutos: documenta tu proceso actual de {topic}. Sí, suena simple, pero el 90% de los negocios exitosos tienen sus procesos documentados. Esto te ayuda a: 1) Identificar cuellos de botella, 2) Delegar tareas, 3) Mejorar consistentemente. Prueba y me cuentas.",
                "delay_hours": delay_hours,
                "type": "value",
                "tip": "Documenta tus procesos",
            },
            {
                "order": 3,
                "subject": f"¿Listo para llevar tu {topic} al siguiente nivel?",
                "content": f"Hemos hablado de estrategia y procesos. Si quieres que analicemos tu situación específica de {topic} y te dé un plan personalizado, solo responde a este mensaje con 'ANALIZAR' y coordinamos una breve llamada sin compromiso. Sin presión, solo valor.",
                "delay_hours": delay_hours,
                "type": "soft_cta",
                "tip": "Análisis personalizado disponible",
            },
        ]
        return messages[:count]

    # ========== Enrollment & Delivery ==========

    async def enroll_lead(
        self,
        sequence_id: uuid.UUID,
        conversation_id: uuid.UUID,
        inbound_lead_id: uuid.UUID = None,
    ) -> ValueSequenceEnrollment:
        """Enroll a lead in a value sequence."""
        sequence = await self._get_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")

        enrollment = ValueSequenceEnrollment(
            business_id=sequence.business_id,
            sequence_id=sequence_id,
            conversation_id=conversation_id,
            inbound_lead_id=inbound_lead_id,
            total_steps=sequence.message_count,
            status="active",
        )
        self.db.add(enrollment)

        # Update sequence stats
        sequence.times_started += 1

        # Update lead stage
        if inbound_lead_id:
            lead = await self.db.get(InboundLead, inbound_lead_id)
            if lead and lead.nurturing_stage == NurturingStage.NEW:
                lead.nurturing_stage = NurturingStage.AWARENESS
                lead.value_touches_received += 1

        await self.db.commit()
        await self.db.refresh(enrollment)
        logger.info(f"Enrolled conversation {conversation_id} in sequence {sequence_id}")
        return enrollment

    async def send_next_message(self, enrollment_id: uuid.UUID) -> dict[str, Any]:
        """Send the next message in a value sequence."""
        enrollment = await self.db.get(ValueSequenceEnrollment, enrollment_id)
        if not enrollment or enrollment.status != "active":
            return {"status": "skipped", "reason": "not_active"}

        sequence = await self._get_sequence(enrollment.sequence_id)
        if not sequence:
            return {"status": "error", "reason": "sequence_not_found"}

        next_step = enrollment.current_step + 1
        if next_step > sequence.message_count:
            enrollment.status = "completed"
            enrollment.completed_at = datetime.now(timezone.utc)
            sequence.times_completed += 1
            await self.db.commit()
            return {"status": "completed"}

        message_data = sequence.messages[next_step - 1] if next_step <= len(sequence.messages) else None
        if not message_data:
            return {"status": "error", "reason": "no_message_data"}

        # Check fatigue
        can_contact = await self.fatigue.can_contact_now(
            enrollment.business_id, enrollment.conversation_id
        )
        if not can_contact.get("allowed", True):
            return {"status": "blocked", "reason": "fatigue", "retry_after_hours": 24}

        # Send message
        from app.domains.channels.services import send_outbound_message
        try:
            await send_outbound_message(
                self.db,
                enrollment.conversation_id,
                message_data.get("content", ""),
                content_type="text",
            )
        except Exception as e:
            logger.error(f"Failed to send value message: {e}")
            return {"status": "error", "reason": str(e)}

        # Update enrollment
        enrollment.current_step = next_step
        enrollment.messages_sent += 1
        enrollment.last_engagement_at = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info(f"Sent value message {next_step}/{sequence.message_count} to enrollment {enrollment_id}")
        return {"status": "sent", "step": next_step, "total": sequence.message_count}

    async def nurture_cold_leads(
        self,
        business_id: uuid.UUID,
        sequence_id: uuid.UUID,
        max_leads: int = 20,
    ) -> dict[str, Any]:
        """Auto-enroll cold leads and send next messages."""
        # Find cold leads without active enrollment
        result = await self.db.execute(
            select(InboundLead).where(
                InboundLead.business_id == business_id,
                InboundLead.nurturing_stage.in_([NurturingStage.NEW, NurturingStage.AWARENESS]),
                InboundLead.is_active == True,
            ).limit(max_leads)
        )
        cold_leads = result.scalars().all()

        enrolled = 0
        messages_sent = 0

        for lead in cold_leads:
            try:
                # Check if already enrolled
                existing = await self.db.execute(
                    select(ValueSequenceEnrollment).where(
                        ValueSequenceEnrollment.inbound_lead_id == lead.id,
                        ValueSequenceEnrollment.status == "active",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                enrollment = await self.enroll_lead(
                    sequence_id=sequence_id,
                    conversation_id=lead.conversation_id,
                    inbound_lead_id=lead.id,
                )
                enrolled += 1

                # Send first message immediately
                result = await self.send_next_message(enrollment.id)
                if result.get("status") == "sent":
                    messages_sent += 1

            except Exception as e:
                logger.error(f"Failed to nurture lead {lead.id}: {e}")

        return {"enrolled": enrolled, "messages_sent": messages_sent}

    # ========== Performance ==========

    async def get_sequence_performance(self, sequence_id: uuid.UUID) -> dict[str, Any]:
        """Get performance metrics for a value sequence."""
        sequence = await self._get_sequence(sequence_id)
        if not sequence:
            return {"error": "Sequence not found"}

        enrollments_result = await self.db.execute(
            select(func.count(ValueSequenceEnrollment.id)).where(
                ValueSequenceEnrollment.sequence_id == sequence_id,
            )
        )
        total_enrollments = enrollments_result.scalar() or 0

        completed_result = await self.db.execute(
            select(func.count(ValueSequenceEnrollment.id)).where(
                ValueSequenceEnrollment.sequence_id == sequence_id,
                ValueSequenceEnrollment.status == "completed",
            )
        )
        completed = completed_result.scalar() or 0

        converted_result = await self.db.execute(
            select(func.count(ValueSequenceEnrollment.id)).where(
                ValueSequenceEnrollment.sequence_id == sequence_id,
                ValueSequenceEnrollment.converted_at.isnot(None),
            )
        )
        converted = converted_result.scalar() or 0

        completion_rate = (completed / total_enrollments * 100) if total_enrollments > 0 else 0
        conversion_rate = (converted / total_enrollments * 100) if total_enrollments > 0 else 0

        return {
            "sequence_id": str(sequence_id),
            "name": sequence.name,
            "topic": sequence.topic,
            "total_enrollments": total_enrollments,
            "completed": completed,
            "converted": converted,
            "completion_rate": round(completion_rate, 2),
            "conversion_rate": round(conversion_rate, 2),
        }

    # ========== Helpers ==========

    async def _get_sequence(self, sequence_id: uuid.UUID) -> Optional[ValueSequence]:
        result = await self.db.execute(
            select(ValueSequence).where(ValueSequence.id == sequence_id)
        )
        return result.scalar_one_or_none()
