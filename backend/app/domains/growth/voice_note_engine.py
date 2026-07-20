"""Voice Note Marketing Engine — Personalized voice notes for WhatsApp.

Voice notes generate 3x higher engagement than text messages.
This engine creates contextual, warm voice note scripts that:
- Sound personal and hand-typed
- Build trust through voice (the most human channel)
- Are used in value sequences, follow-ups, and warming campaigns
- Support multiple languages and tones
"""

import uuid
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.outreach.service import FatigueScoringService
from app.core.logger import get_logger

logger = get_logger(__name__)


class VoiceNoteEngine:
    """Generates personalized voice note scripts for maximum impact."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    async def generate_welcome_voice_note(
        self,
        business_id: uuid.UUID,
        lead_name: str,
        source: str = "organic",
    ) -> str:
        """Generate a warm welcome voice note script."""
        system_prompt = """Eres un emprendedor argentino exitoso que graba notas de voz para WhatsApp.
Escribes SCRIPTS de notas de voz, no el audio.

Reglas para notas de voz de ventas:
1. Máximo 45 segundos de lectura (90-110 palabras)
2. Tono: cálido, casual, como hablando con un amigo
3. Emojis de voz: "mmm", "che", "mirá", "la verdad", "tipo"
4. Siempre personaliza con el nombre
5. Una sola idea por nota de voz
6. Termina con una pregunta abierta SUAVE
7. NO sonar como telemarketer
8. Incluye [PAUSA] donde harías una pausa natural"""

        user_prompt = f"""Escribe el script de una nota de voz de bienvenida para un nuevo lead que llegó por {source}.

Nombre del lead: {lead_name}

La nota debe:
- Saludar por nombre
- Agradecer el contacto
- Mencionar brevemente qué hacés (sin vender)
- Preguntar algo sobre su situación actual
- Sonar como una nota de voz REAL (con muletillas naturales)

Ejemplo de tono:
"Che Juan, cómo andás? Mirá, te escribo porque... la verdad me copó que hayas llegado por Instagram. Yo lo que hago es ayudar a emprendedores a [tema]. Pero contame, vos en qué andás ahora?"

Responde SOLO el script, sin explicaciones."""

        try:
            script = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8,
            )
            return script or self._fallback_welcome(lead_name)
        except Exception as e:
            logger.error(f"Voice note generation failed: {e}")
            return self._fallback_welcome(lead_name)

    async def generate_value_voice_note(
        self,
        business_id: uuid.UUID,
        lead_name: str,
        topic: str,
        tip: str,
    ) -> str:
        """Generate a value-bomb voice note script."""
        system_prompt = """Eres un mentor que comparte tips valiosos por nota de voz de WhatsApp.
Escribes SCRIPTS de notas de voz.

Reglas:
1. Máximo 40 segundos (80-100 palabras)
2. UN solo tip práctico
3. Tono: "che, te cuento algo que descubrí..."
4. Incluye [PAUSA] para pausas naturales
5. Termina con "¿qué te parece?" o similar"""

        user_prompt = f"""Escribe un script de nota de voz para {lead_name} sobre: {topic}

El tip a compartir: {tip}

Ejemplo:
"Che {lead_name}, te cuento algo que descubrí la semana pasada... [PAUSA] La mayoría de los negocios fallan no porque el producto sea malo, sino porque no tienen un sistema de seguimiento. [PAUSA] Yo lo que hago es... bla bla. ¿Vos tenés algún sistema o estás tirando magia?"

Responde SOLO el script."""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8,
            ) or self._fallback_value(lead_name, tip)
        except Exception as e:
            logger.error(f"Value voice note failed: {e}")
            return self._fallback_value(lead_name, tip)

    async def generate_soft_close_voice_note(
        self,
        business_id: uuid.UUID,
        lead_name: str,
        product_name: str,
    ) -> str:
        """Generate a soft-close voice note that doesn't sound salesy."""
        system_prompt = """Eres un vendedor que NUNCA suena a vendedor.
Escribes scripts de notas de voz para cerrar suavemente.

Reglas:
1. Máximo 35 segundos (70-90 palabras)
2. NO mencionar precio
3. NO presionar
4. Ofrecer ayuda, no vender producto
5. Tono: "che, si querés que veamos juntos tu situación..."
6. Incluir [PAUSA]"""

        user_prompt = f"""Escribe un script de nota de voz de cierre suave para {lead_name}.

Producto/servicio: {product_name}

Debe sonar como:
"Che {lead_name}, mira... no sé si esto te sirve a vos, pero si querés que veamos juntos cómo está tu situación y te doy una opinión sincera, avisame. [PAUSA] No te voy a vender nada, te lo juro. [PAUSA] Pero capaz te puedo ahorrar un par de dolores de cabeza. ¿Te pinta?"

Responde SOLO el script."""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8,
            ) or self._fallback_close(lead_name)
        except Exception as e:
            logger.error(f"Close voice note failed: {e}")
            return self._fallback_close(lead_name)

    async def generate_referral_voice_note(
        self,
        business_id: uuid.UUID,
        customer_name: str,
        code: str,
    ) -> str:
        """Generate a natural referral request voice note."""
        system_prompt = """Eres un emprendedor agradecido que pide referidos a sus clientes felices.
Escribes scripts de notas de voz para WhatsApp.

Reglas:
1. Máximo 30 segundos
2. Agradecer primero
3. Pedir el referido como favor personal
4. Mencionar que ambos ganan algo
5. Tono: "che, te jodo con una cosita..."""

        user_prompt = f"""Escribe un script de nota de voz pidiendo un referido a {customer_name}.

Código de referido: {code}

Ejemplo:
"Che {customer_name}, te jodo con una cosita... [PAUSA] Mirá, la verdad me está yendo re bien con el negocio y eso en parte es gracias a gente como vos que confió. [PAUSA] Si conocés a alguien que esté pasando por [problema], ¿me lo recomendás? Usá el código {code} y los dos se benefician. [PAUSA] Solo si se te ocurre alguien, eh. No pasa nada si no. Un abrazo!"

Responde SOLO el script."""

        try:
            return await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8,
            ) or self._fallback_referral(customer_name, code)
        except Exception as e:
            logger.error(f"Referral voice note failed: {e}")
            return self._fallback_referral(customer_name, code)

    def _fallback_welcome(self, name: str) -> str:
        return f"Hola {name}! Gracias por escribirme. Te cuento brevemente: yo ayudo a emprendedores a vender más sin depender de los anuncios pagos. Pero contame, ¿en qué andás vos ahora?"

    def _fallback_value(self, name: str, tip: str) -> str:
        return f"Che {name}, te cuento algo rápido... {tip}. Probá y me contás cómo te fue."

    def _fallback_close(self, name: str) -> str:
        return f"{name}, si querés que charlemos 10 minutos sobre tu situación y te doy una opinión sincera, avisame. Sin compromiso."

    def _fallback_referral(self, name: str, code: str) -> str:
        return f"{name}, si conocés a alguien que le pueda servir lo que hago, usá el código {code}. Los dos se benefician. Gracias!"
