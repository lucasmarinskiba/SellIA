"""Onboarding Mágico — Analyzer con IA"""

import json
from typing import Any
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.onboarding.schemas import BusinessDiscovery, ScrapedProduct

logger = get_logger(__name__)

SYSTEM_PROMPT = """ sos un analista experto en negocios y marketing digital.
Recibís texto extraído de una página web o Instagram de un negocio.
Tu tarea es analizar el texto y devolver un JSON estricto con la siguiente estructura:

{
  "name": "Nombre del negocio (máx 60 chars)",
  "description": "Descripción corta y atractiva del negocio (2-3 oraciones)",
  "type": "services|goods|digital|mixed",
  "tone_of_voice": "Descripción del tono de comunicación (ej: cercano y profesional, luxury, joven y divertido)",
  "brand_colors": ["#HEX1", "#HEX2"],
  "target_audience": "Público objetivo detectado",
  "products": [
    {
      "name": "Nombre del producto/servicio",
      "description": "Descripción breve",
      "price": null,
      "currency": "ARS",
      "category": "categoría"
    }
  ],
  "suggested_agents": [
    {"slug": "consultor", "name": "Consultor de Ventas", "emoji": "🧠", "tagline": "Asesoramiento experto", "description": "...", "expertise": ["ventas", "consultoría"], "color": "#FF6B35"}
  ],
  "suggested_workflows": [
    {"name": "Bienvenida automática", "description": "...", "trigger_type": "new_conversation", "actions": [...]}
  ]
}

REGLAS:
- Si no hay precios visibles, usa null para price.
- Detectá hasta 6 productos/servicios principales.
- El tipo de negocio inferilo del contenido (servicios = consultoría/salud/etc, goods = productos físicos, digital = cursos/software, mixed = mixto).
- Los suggested_agents deben ser 2-3 agentes relevantes para el tipo de negocio.
- Los suggested_workflows deben ser 2-3 automatizaciones útiles (bienvenida, seguimiento, recuperación de carrito/abandono).
- Devolvé SOLO el JSON válido, sin markdown, sin explicaciones."""


class OnboardingAnalyzer:
    """Analiza texto scrapeado con IA para extraer datos estructurados de negocio."""

    def __init__(self):
        self.settings = get_settings()

    async def analyze(self, raw_text: str) -> BusinessDiscovery:
        """Envía el texto a la IA y devuelve BusinessDiscovery."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Texto extraído del sitio web/Instagram:\n\n{raw_text}\n\nDevolvé el JSON."},
                ],
                temperature=0.3,
                max_tokens=2500,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Normalizar productos
            products = []
            for p in data.get("products", []):
                try:
                    from decimal import Decimal
                    price = Decimal(str(p["price"])) if p.get("price") else None
                    products.append(ScrapedProduct(
                        name=p["name"],
                        description=p.get("description"),
                        price=price,
                        currency=p.get("currency", "ARS"),
                        category=p.get("category"),
                    ))
                except Exception:
                    continue

            return BusinessDiscovery(
                name=data.get("name", "Mi Negocio"),
                description=data.get("description"),
                type=data.get("type", "services"),
                tone_of_voice=data.get("tone_of_voice"),
                brand_colors=data.get("brand_colors", []),
                target_audience=data.get("target_audience"),
                products=products,
                suggested_agents=data.get("suggested_agents", []),
                suggested_workflows=data.get("suggested_workflows", []),
            )
        except Exception as e:
            logger.error(f"Error analizando con IA: {e}")
            # Fallback: devolver mínimo viable
            return BusinessDiscovery(
                name="Mi Negocio",
                description="Negocio detectado automáticamente",
                type="services",
                products=[],
                suggested_agents=[],
                suggested_workflows=[],
            )
