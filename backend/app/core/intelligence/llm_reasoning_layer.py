"""
LLM Reasoning Layer — Integración REAL con Claude API.

Antes: Brain decide basado en templates + heurísticas
Después: Claude razona en tiempo real sobre situación específica

Mayor inteligencia, reasoning profundo, adaptación a contexto real.
"""

import logging
import anthropic
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LLMReasoningLayer:
    """Capa de reasoning con Claude API (real, no simulado)."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # ========== REASONING ==========

    async def reason_about_situation(
        self,
        situation: Dict[str, Any],
        knowledge_context: str,
    ) -> Dict[str, Any]:
        """
        Claude razona profundamente sobre situación específica.

        Recibe: situación actual + context conocimiento
        Retorna: análisis razonado + recomendaciones + insights
        """

        logger.info("Claude reasoning: analyzing situation")

        prompt = f"""
SITUACION ACTUAL:
{self._format_situation(situation)}

CONOCIMIENTO DISPONIBLE:
{knowledge_context}

TAREA:
Analiza profundamente esta situación de negocio/ventas.

Considera:
1. Factores clave que impactan decisión
2. Riesgos y oportunidades
3. Estrategia óptima según contexto
4. Tácticas específicas de ejecución
5. Métricas de éxito

Responde en JSON estructurado con análisis, recomendaciones, confianza.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Parse JSON from response
            import json

            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # Extract JSON if wrapped in text
                import re

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                analysis = json.loads(json_match.group(0)) if json_match else {"reasoning": response_text}

            return {
                "status": "success",
                "analysis": analysis,
                "model": self.model,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            }

        except Exception as e:
            logger.error(f"Claude reasoning failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def generate_copy(
        self,
        product: Dict[str, Any],
        style: str,
        audience: str,
    ) -> Dict[str, Any]:
        """
        Claude genera copy persuasivo REAL para vender producto.
        """

        prompt = f"""
PRODUCTO:
Nombre: {product.get('name')}
Descripción: {product.get('description')}
Precio: {product.get('price')}
Categoría: {product.get('category')}

ESTILO:
{style}

AUDIENCIA:
{audience}

TAREA:
Crea copy persuasivo, emotivo y específico para vender este producto.

Genera:
1. Titular (hook impactante)
2. Descripción (problema → solución → proof)
3. Call-to-action (urgencia)
4. Variantes A/B para testing

Responde en JSON con copy estructurado.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            import re

            response_text = message.content[0].text
            try:
                copy = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                copy = json.loads(json_match.group(0)) if json_match else {"copy": response_text}

            return {"status": "success", "copy": copy}

        except Exception as e:
            logger.error(f"Copy generation failed: {str(e)}")
            return {"status": "error"}

    async def analyze_buyer_psychology(
        self,
        buyer_profile: Dict[str, Any],
        product: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Claude analiza psicología del buyer + recomienza estrategia personalizada.
        """

        prompt = f"""
PERFIL COMPRADOR:
{self._format_buyer(buyer_profile)}

PRODUCTO:
{self._format_product(product)}

TAREA:
Analiza profundamente la psicología de este comprador específico.

Identifica:
1. Motivaciones principales (qué lo mueve)
2. Objecciones anticipadas
3. Triggers psicológicos efectivos
4. Framing óptimo (cómo presentar producto)
5. Estrategia de cierre personalizada

Responde con estrategia de venta PERSONALIZADA.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            import re

            response_text = message.content[0].text
            try:
                strategy = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                strategy = json.loads(json_match.group(0)) if json_match else {"strategy": response_text}

            return {"status": "success", "strategy": strategy}

        except Exception as e:
            logger.error(f"Psychology analysis failed: {str(e)}")
            return {"status": "error"}

    async def negotiate_with_buyer(
        self,
        buyer_message: str,
        negotiation_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Claude sugiere siguiente move en negociación.
        """

        prompt = f"""
ESTADO NEGOCIACION:
Precio inicial: {negotiation_state.get('initial_price')}
Precio actual: {negotiation_state.get('current_price')}
Ofertas previas: {negotiation_state.get('offers', [])}

MENSAJE COMPRADOR:
"{buyer_message}"

TAREA:
¿Cuál es el siguiente move óptimo en esta negociación?

Considera:
1. Qué está pidiendo el buyer (real vs superficial)
2. Cuál es nuestro límite (margin, walk-away price)
3. Leverage disponible (escasez, urgencia, alternativas)
4. Next concession (qué podemos ofrecer sin perder margen)
5. Cierre probable

Responde con recomendación estratégica.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            return {"status": "success", "recommendation": response_text}

        except Exception as e:
            logger.error(f"Negotiation suggestion failed: {str(e)}")
            return {"status": "error"}

    async def evaluate_market_opportunity(
        self,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Claude evalúa oportunidad de mercado.
        """

        prompt = f"""
DATOS MERCADO:
{self._format_market(market_data)}

TAREA:
Evalúa esta oportunidad de mercado:

1. Tamaño del mercado (total addressable)
2. Competencia + diferenciación posible
3. Entrada + escalabilidad
4. Timing (es ahora el momento?)
5. Riesgos principales
6. Score oportunidad (0-100)

Responde con evaluación profesional.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            import re

            response_text = message.content[0].text
            try:
                evaluation = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                evaluation = json.loads(json_match.group(0)) if json_match else {"evaluation": response_text}

            return {"status": "success", "evaluation": evaluation}

        except Exception as e:
            logger.error(f"Market evaluation failed: {str(e)}")
            return {"status": "error"}

    # ========== FORMATTING HELPERS ==========

    def _format_situation(self, situation: Dict[str, Any]) -> str:
        return f"""
Plataforma: {situation.get('platform')}
Acción: {situation.get('action_type')}
Contexto: {situation.get('context', {})}
Tiempo: {situation.get('timestamp', 'now')}
"""

    def _format_buyer(self, buyer: Dict[str, Any]) -> str:
        return f"""
Tipo: {buyer.get('type')}
Budget: {buyer.get('budget')}
Psicología: {buyer.get('psychology')}
Objecciones: {buyer.get('objections', [])}
Comportamiento previo: {buyer.get('history', [])}
"""

    def _format_product(self, product: Dict[str, Any]) -> str:
        return f"""
Nombre: {product.get('name')}
Precio: {product.get('price')}
Margen: {product.get('margin')}
Categoría: {product.get('category')}
Competencia precio: {product.get('competitor_price')}
"""

    def _format_market(self, market: Dict[str, Any]) -> str:
        return f"""
Demanda: {market.get('demand')}
Competencia: {market.get('competitors', 0)} jugadores
Precio promedio: {market.get('avg_price')}
Crecimiento: {market.get('growth_rate')}
Saturation: {market.get('saturation_level')}
"""
