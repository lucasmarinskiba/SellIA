"""SellIA Brain Service — Estrategias + Prompts para Computer Use.

Expone SellIA Brain como servicio consumible:
- Consultar estrategia óptima por contexto
- Obtener prompts/tácticas por etapa de venta
- Decision intelligence para automatización

Conecta: BrainIntegrationLayer → Computer Use Sessions
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SalesStage(str, Enum):
    """Etapas del pipeline de venta."""
    AWARENESS = "awareness"          # Conocer el producto
    CONSIDERATION = "consideration"  # Evaluar opciones
    DECISION = "decision"           # Decidir comprar
    NEGOTIATION = "negotiation"     # Negociar términos
    CLOSURE = "closure"             # Cerrar venta
    ONBOARDING = "onboarding"       # Post-venta
    RETENTION = "retention"         # Mantener cliente


class Platform(str, Enum):
    """Plataformas de venta/comunicación."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    MERCADOLIBRE = "mercadolibre"
    AMAZON = "amazon"
    WEBSITE = "website"
    LINKEDIN = "linkedin"


class ActionContext:
    """Contexto para decidir acción óptima."""

    def __init__(
        self,
        platform: Platform,
        stage: SalesStage,
        customer_profile: Optional[Dict[str, Any]] = None,
        product_info: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        objections: Optional[List[str]] = None,
    ):
        self.platform = platform
        self.stage = stage
        self.customer_profile = customer_profile or {}
        self.product_info = product_info or {}
        self.conversation_history = conversation_history or []
        self.objections = objections or []
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "stage": self.stage.value,
            "customer_profile": self.customer_profile,
            "product_info": self.product_info,
            "conversation_history_length": len(self.conversation_history),
            "objections": self.objections,
        }


class StrategyRecommendation:
    """Recomendación de estrategia del Brain."""

    def __init__(
        self,
        strategy_id: str,
        strategy_name: str,
        stage: SalesStage,
        confidence: float,
        tactics: List[str],
        prompt_template: str,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.stage = stage
        self.confidence = confidence  # 0-1
        self.tactics = tactics
        self.prompt_template = prompt_template
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "stage": self.stage.value,
            "confidence": self.confidence,
            "tactics": self.tactics,
            "prompt_template": self.prompt_template,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }


class SellIABrainService:
    """Servicio que expone SellIA Brain para Computer Use."""

    # Estrategias por etapa (placeholder — se cargan desde prompts/)
    _STAGE_STRATEGIES = {
        SalesStage.AWARENESS: [
            "attention_grabber",
            "value_prop_teaser",
            "social_proof",
        ],
        SalesStage.CONSIDERATION: [
            "feature_comparison",
            "objection_handler",
            "alternative_analysis",
        ],
        SalesStage.DECISION: [
            "limited_time_offer",
            "scarcity_trigger",
            "closing_technique",
        ],
        SalesStage.NEGOTIATION: [
            "price_justifier",
            "payment_terms",
            "bundle_upsell",
        ],
        SalesStage.CLOSURE: [
            "order_confirmation",
            "payment_link",
            "calendar_scheduling",
        ],
        SalesStage.ONBOARDING: [
            "welcome_sequence",
            "setup_guide",
            "first_success",
        ],
        SalesStage.RETENTION: [
            "check_in_message",
            "upsell_opportunity",
            "loyalty_offer",
        ],
    }

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.logger = logger

    async def get_strategy(
        self,
        context: ActionContext,
    ) -> Optional[StrategyRecommendation]:
        """
        Consulta Brain para obtener estrategia óptima.

        Analiza contexto + historial → recomienda estrategia de ventas.
        """
        cache_key = self._get_cache_key(context)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. Obtener estrategias candidatas para la etapa
        candidates = self._STAGE_STRATEGIES.get(context.stage, [])

        # 2. Filtrar por plataforma + customer profile
        best_strategy = self._rank_strategies(
            candidates,
            context,
        )

        # 3. Construir recomendación
        if not best_strategy:
            return None

        recommendation = StrategyRecommendation(
            strategy_id=best_strategy["id"],
            strategy_name=best_strategy["name"],
            stage=context.stage,
            confidence=best_strategy.get("confidence", 0.8),
            tactics=best_strategy.get("tactics", []),
            prompt_template=await self._get_prompt_template(best_strategy["id"]),
            reasoning=best_strategy.get("reasoning", "Context-matched strategy"),
            metadata={"platform": context.platform.value},
        )

        # 4. Cache result
        self.cache[cache_key] = recommendation

        self.logger.info(
            f"Strategy recommended: {best_strategy['name']} "
            f"for {context.stage.value} on {context.platform.value}"
        )

        return recommendation

    async def get_response_prompt(
        self,
        context: ActionContext,
        instruction: str,
    ) -> str:
        """
        Genera prompt completo para responder mensaje.

        Combina:
        - Sistema: persona + brand voice
        - Contexto: customer profile + historial
        - Instrucción: qué debe lograr
        """
        strategy = await self.get_strategy(context)

        if not strategy:
            return self._get_default_prompt(context)

        prompt = f"""You are SellIA, an intelligent sales agent.

Customer Context:
- Profile: {context.customer_profile}
- Stage: {context.stage.value}
- Objections: {', '.join(context.objections) if context.objections else 'None'}

Strategy: {strategy.strategy_name}
Tactics: {', '.join(strategy.tactics)}

Instructions: {instruction}

Respond with a message that:
1. Follows the {strategy.strategy_name} strategy
2. Uses tactics: {', '.join(strategy.tactics)}
3. Maintains authentic brand voice
4. Handles objections if present
5. Moves toward next stage

Template:
{strategy.prompt_template}
"""
        return prompt

    async def score_lead(
        self,
        conversation: List[Dict[str, str]],
        customer_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Scoring automático de lead (hot/warm/cold).

        Analiza conversación + perfil → score 0-100 + recomendación.
        """
        # Placeholder — será conectado al Lead Qualifier agent
        score = 0
        signals = []

        # Señales positivas
        if len(conversation) > 3:
            score += 20
            signals.append("Multiple interactions")

        if customer_profile.get("budget_mentioned"):
            score += 30
            signals.append("Budget disclosed")

        if customer_profile.get("timeline"):
            score += 25
            signals.append("Timeline indicated")

        # Determinar temperatura
        if score >= 70:
            temperature = "hot"
        elif score >= 40:
            temperature = "warm"
        else:
            temperature = "cold"

        return {
            "score": score,
            "temperature": temperature,
            "signals": signals,
            "recommended_action": self._recommend_lead_action(temperature),
        }

    async def detect_sales_signals(
        self,
        message: str,
        context: ActionContext,
    ) -> Dict[str, Any]:
        """
        Detecta señales de compra en mensaje.

        Identifica palabras clave → recomienda cierre.
        """
        buying_signals = [
            "cuánto", "precio", "costo", "how much", "cost",
            "cuándo", "when", "ready", "listo",
            "garantía", "warranty", "envío", "shipping",
            "descuento", "discount", "oferta", "offer",
            "puedo", "can i", "dónde", "where", "how",
        ]

        signal_detected = any(signal in message.lower() for signal in buying_signals)

        if signal_detected:
            return {
                "signal_found": True,
                "signal_type": self._classify_signal(message),
                "recommended_action": "move_to_closure",
                "confidence": 0.85,
            }

        return {
            "signal_found": False,
            "signal_type": None,
            "recommended_action": "continue_nurture",
            "confidence": 0.9,
        }

    # ── Private ──────────────────────────────────────────────────────

    def _get_cache_key(self, context: ActionContext) -> str:
        return f"{context.stage.value}:{context.platform.value}:{hash(str(context.objections))}"

    def _rank_strategies(
        self,
        candidates: List[str],
        context: ActionContext,
    ) -> Optional[Dict[str, Any]]:
        """Elige mejor estrategia de candidatos."""
        if not candidates:
            return None

        # Placeholder — será mejorado con ML
        return {
            "id": candidates[0],
            "name": candidates[0].replace("_", " ").title(),
            "tactics": ["authentic_approach", "value_first", "ask_permission"],
            "confidence": 0.85,
            "reasoning": f"Optimal for {context.stage.value} stage on {context.platform.value}",
        }

    async def _get_prompt_template(self, strategy_id: str) -> str:
        """Obtiene template de prompt para estrategia."""
        # Placeholder — se cargaría desde prompts/categories
        return f"Use {strategy_id} approach. Be authentic and value-focused."

    def _get_default_prompt(self, context: ActionContext) -> str:
        """Prompt default si Brain no da recomendación."""
        return f"""You are SellIA, sales agent.

Stage: {context.stage.value}
Platform: {context.platform.value}

Be helpful, authentic, and focused on customer value.
Listen before selling. Ask permission before pitching.
"""

    def _classify_signal(self, message: str) -> str:
        """Clasifica tipo de señal de compra."""
        if any(w in message.lower() for w in ["precio", "cost", "cuánto", "how much"]):
            return "price_inquiry"
        if any(w in message.lower() for w in ["cuándo", "when", "ready", "listo"]):
            return "timeline_commitment"
        if any(w in message.lower() for w in ["envío", "shipping", "dónde", "where"]):
            return "delivery_logistics"
        return "general_interest"

    def _recommend_lead_action(self, temperature: str) -> str:
        """Acción recomendada por temperatura."""
        return {
            "hot": "close_now",
            "warm": "nurture_then_close",
            "cold": "re_engage_with_value",
        }.get(temperature, "nurture")


# Singleton instance
_brain_service: Optional[SellIABrainService] = None


def get_brain_service() -> SellIABrainService:
    """Obtiene instancia del servicio Brain."""
    global _brain_service
    if _brain_service is None:
        _brain_service = SellIABrainService()
    return _brain_service
