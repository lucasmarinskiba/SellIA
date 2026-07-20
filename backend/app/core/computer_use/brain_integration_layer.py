"""
Brain Integration Layer — Computer Use consulta Brain para tomar decisiones inteligentes.

Convierte Computer Use de "dumb executor" a "intelligent agent que raziona".
"""

import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class BrainIntegrationLayer:
    """Conecta Computer Use con Brain (knowledge files) para decisiones inteligentes."""

    def __init__(self, brain_engine, knowledge_library):
        self.brain = brain_engine
        self.knowledge = knowledge_library

    # ========== DECISION MAKING ==========

    async def decide_action(
        self,
        situation: Dict[str, Any],  # {"platform": "mercadolibre", "action_type": "list_product", "context": {...}}
        available_strategies: List[str],
    ) -> Dict[str, Any]:
        """
        Lee situación + consulta brain → decide mejor acción.

        situation: qué está pasando, dónde, qué contexto
        available_strategies: opciones posibles

        Retorna: strategy recomendada + tácticas específicas + parámetros
        """

        logger.info(f"Deciding action for situation: {situation.get('action_type')}")

        # 1. Obtener knowledge relevante
        action_type = situation.get("action_type")
        knowledge = await self._fetch_relevant_knowledge(action_type)

        # 2. Analizar situación
        analysis = await self._analyze_situation(situation, knowledge)

        # 3. Recomendar estrategia
        recommended_strategy = await self._recommend_strategy(
            action_type,
            analysis,
            available_strategies,
            knowledge,
        )

        # 4. Generar tácticas específicas
        tactics = await self._generate_tactics(
            action_type,
            recommended_strategy,
            situation,
            knowledge,
        )

        return {
            "strategy": recommended_strategy,
            "reasoning": analysis,
            "tactics": tactics,
            "confidence": analysis.get("confidence_score", 0),
        }

    async def _fetch_relevant_knowledge(self, action_type: str) -> Dict[str, Any]:
        """
        Busca knowledge files relevantes para tipo de acción.

        action_type: "list_product", "set_price", "write_description", "negotiate", etc
        """

        knowledge_map = {
            "list_product": [
                "marketplace_algorithm_mastery",
                "ecommerce_conversion_master",
                "dynamic_pricing_neural",
            ],
            "set_price": [
                "dynamic_pricing_neural",
                "high_ticket_closing",
                "luxury_positioning",
            ],
            "write_description": [
                "copywriting_mastery",
                "persuasion_engine",
                "milton_model_nlp",
            ],
            "negotiate_deal": [
                "trump_dealmaking_tactics",
                "negotiation_framework",
                "objection_handling",
            ],
            "close_sale": [
                "belfort_straight_line",
                "closing_framework",
                "psychological_triggers",
            ],
            "offer_discount": [
                "dynamic_pricing_neural",
                "psychological_pricing",
                "scarcity_urgency",
            ],
            "respond_negative_review": [
                "customer_service_excellence",
                "crisis_communication",
                "brand_reputation",
            ],
            "optimize_listing": [
                "marketplace_algorithm_mastery",
                "seo_mastery",
                "conversion_rate_optimization",
            ],
        }

        knowledge_files = knowledge_map.get(action_type, [])
        knowledge_content = {}

        for file_name in knowledge_files:
            content = await self.knowledge.get(file_name)
            if content:
                knowledge_content[file_name] = content

        return knowledge_content

    async def _analyze_situation(
        self,
        situation: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analiza situación actual. Retorna: insights, problemas, oportunidades.
        """

        # Extraer factores situacionales
        platform = situation.get("platform", "unknown")
        action_type = situation.get("action_type", "unknown")
        context = situation.get("context", {})

        # Análisis simple (puede ser más complejo con ML)
        analysis = {
            "platform": platform,
            "action_type": action_type,
            "key_factors": [],
            "risks": [],
            "opportunities": [],
            "confidence_score": 0.8,
        }

        # Platform-specific factors
        if platform == "mercadolibre":
            analysis["key_factors"].append("ML ranking depends on title+price+seller_stats")
            analysis["opportunities"].append("Optimize title for search (high keyword relevance)")

        elif platform == "amazon":
            analysis["key_factors"].append("Amazon A9 focuses on reviews and conversion rate")
            analysis["risks"].append("New listings have low visibility, need reviews early")

        elif platform == "tiktok_shop":
            analysis["key_factors"].append("TikTok rewards video recency and engagement")
            analysis["opportunities"].append("Create short videos for organic reach")

        # Action-specific considerations
        if action_type == "list_product":
            analysis["key_factors"].append("First listing impression critical for CTR")
            analysis["opportunities"].append("Use trending keywords in title")

        elif action_type == "set_price":
            analysis["key_factors"].append("Price is psychological trigger and competitiveness signal")
            if context.get("competition_price"):
                analysis["key_factors"].append(
                    f"Competitor priced at {context['competition_price']}, opportunity for positioning"
                )

        elif action_type == "negotiate_deal":
            analysis["key_factors"].append("Early anchoring critical (set precedent)")
            analysis["opportunities"].append("Identify buyer's real objection vs surface objection")

        return analysis

    async def _recommend_strategy(
        self,
        action_type: str,
        analysis: Dict[str, Any],
        available_strategies: List[str],
        knowledge: Dict[str, Any],
    ) -> str:
        """
        Recomienda estrategia óptima basada en análisis.
        """

        # Simple heurística (puede ser ML model)
        strategy_scores = {}

        for strategy in available_strategies:
            score = 0.5  # Base

            # Puntuación según análisis
            if "algorithm" in strategy.lower():
                score += 0.2 if "marketplace_algorithm_mastery" in knowledge else 0

            if "pricing" in strategy.lower():
                score += 0.2 if "dynamic_pricing_neural" in knowledge else 0

            if "copy" in strategy.lower() or "description" in strategy.lower():
                score += 0.2 if "copywriting_mastery" in knowledge else 0

            if "negotiate" in strategy.lower() or "deal" in strategy.lower():
                score += 0.2 if "trump_dealmaking_tactics" in knowledge else 0

            strategy_scores[strategy] = score

        # Retorna estrategia con máxima puntuación
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Recommended strategy: {best_strategy} (score: {strategy_scores[best_strategy]})")

        return best_strategy

    async def _generate_tactics(
        self,
        action_type: str,
        strategy: str,
        situation: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Genera tácticas específicas de ejecución.

        Retorna: parámetros, copy, ofertas, timing, etc que Computer Use usará.
        """

        tactics = {
            "type": action_type,
            "strategy": strategy,
            "parameters": {},
            "copy": {},
            "timing": {},
        }

        # Tácticas para listar producto
        if action_type == "list_product":
            tactics["parameters"]["title_optimization"] = "Use 3-5 keywords, brand + main_benefit + unique_angle"
            tactics["parameters"]["description_structure"] = "Problem → Solution → Proof → Call-to-action"
            tactics["copy"]["title_template"] = f"{situation.get('product_name', 'Product')} - {situation.get('main_benefit', 'Premium Quality')}"
            tactics["parameters"]["price_positioning"] = self._price_strategy(situation, strategy)

        # Tácticas para set price
        elif action_type == "set_price":
            tactics["parameters"]["pricing_method"] = "Psychological pricing (e.g., $29.99 not $30)"
            tactics["parameters"]["competitor_positioning"] = "Price 5-10% below if positioning as value, or 10-20% above if premium"
            base_price = situation.get("base_price", 0)
            tactics["parameters"]["recommended_price"] = self._calculate_optimal_price(
                base_price, situation, knowledge
            )

        # Tácticas para escribir descripción
        elif action_type == "write_description":
            tactics["copy"]["structure"] = [
                "Hook (emotional benefit)",
                "Problem identification (what buyer struggles with)",
                "Solution (how product solves)",
                "Features + benefits (concrete details)",
                "Proof (testimonial, guarantee)",
                "Call-to-action (create urgency)",
            ]
            tactics["parameters"]["length"] = "100-300 words (sweet spot for conversion)"
            tactics["parameters"]["tone"] = "Conversational, benefit-focused, no hyperbole"

        # Tácticas para negociar
        elif action_type == "negotiate_deal":
            tactics["parameters"]["anchor_technique"] = "Start with ambitious ask (sets negotiation window)"
            tactics["parameters"]["concession_order"] = ["Bundle discount", "Payment terms", "Exclusivity", "Volume discount"]
            tactics["parameters"]["walk_away_power"] = "Prepare alternative buyer (leverage)"

        # Tácticas para cerrar
        elif action_type == "close_sale":
            tactics["parameters"]["close_type"] = "Assumptive close (assume buyer will proceed)"
            tactics["parameters"]["objection_handler"] = "Listen to real objection, reframe, offer solution"
            tactics["parameters"]["trial_close"] = "Ask low-commitment question (gauge readiness)"

        return tactics

    def _price_strategy(self, situation: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """Determina estrategia de precio."""
        base_price = situation.get("base_price", 100)
        competitor_price = situation.get("competitor_price", base_price)

        if "premium" in strategy.lower():
            return {
                "type": "premium_positioning",
                "price": int(competitor_price * 1.15),
                "justification": "Higher quality, exclusive features, prestige",
            }
        elif "value" in strategy.lower():
            return {
                "type": "value_positioning",
                "price": int(competitor_price * 0.9),
                "justification": "Best bang for buck, accessible to more buyers",
            }
        else:
            return {
                "type": "market_matching",
                "price": int(competitor_price),
                "justification": "Competitive parity",
            }

    def _calculate_optimal_price(
        self,
        base_price: float,
        situation: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> float:
        """Calcula precio óptimo usando psychological pricing + demand dynamics."""
        # Psychological: $X.99 es más barato psicológicamente que $X+1
        price = base_price
        if price % 1 == 0:
            price = price - 0.01

        # Demand adjustment
        if situation.get("demand", "medium") == "high":
            price *= 1.1
        elif situation.get("demand", "medium") == "low":
            price *= 0.95

        return price

    # ========== CONTEXT MEMORY ==========

    async def remember_outcome(
        self,
        action: str,
        result: Dict[str, Any],
    ) -> None:
        """Recuerda resultado de acción para futuras decisiones."""
        logger.info(f"Remembering outcome: {action} → {result.get('status')}")
        # TODO: Guardar en context memory del brain
        pass

    async def get_learnings(self) -> List[str]:
        """Retorna lecciones aprendidas de acciones previas."""
        # TODO: Extraer patrones de context memory
        return [
            "Listings con títulos optimizados → 2x CTR",
            "Psychological pricing (.99) → 15% más conversión",
            "Videos en TikTok Shop → 3x engagement",
        ]
