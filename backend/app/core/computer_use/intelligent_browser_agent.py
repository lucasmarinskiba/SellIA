"""
Intelligent Browser Agent — Computer Use que PIENSA antes de actuar.

Usa Brain para razonar, adapta en tiempo real, es genio de negocios.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class IntelligentBrowserAgent:
    """Browser automation que consulta brain, toma decisiones, adapta estrategia."""

    def __init__(self, advanced_browser_agent, brain_integration_layer):
        self.browser = advanced_browser_agent
        self.brain = brain_integration_layer
        self.context_memory = {}
        self.action_history = []

    # ========== INTELLIGENT LISTING ==========

    async def intelligent_list_product(
        self,
        product: Dict[str, Any],
        platform: str,
        market_conditions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Lista producto INTELIGENTEMENTE.

        1. Consulta brain → decide strategy (premium/value/volume)
        2. Genera título/descripción/precio óptimos
        3. Ejecuta via Computer Use
        4. Monitorea resultado, adapta si necesario
        """

        logger.info(f"Intelligent listing: {product.get('name')} on {platform}")

        # 1. Analizar situación
        situation = {
            "platform": platform,
            "action_type": "list_product",
            "context": {
                "product_name": product.get("name"),
                "product_category": product.get("category"),
                "base_price": product.get("price"),
                "competition_price": market_conditions.get("competitor_price") if market_conditions else None,
                "demand": market_conditions.get("demand", "medium") if market_conditions else "medium",
            },
        }

        # 2. Consultar brain
        decision = await self.brain.decide_action(
            situation,
            available_strategies=["premium_positioning", "value_positioning", "volume_positioning"],
        )

        # 3. Generar copy optimizado
        optimized_product = await self._optimize_product_copy(product, decision)

        # 4. Ejecutar listing
        listing_result = await self._execute_listing(optimized_product, platform)

        # 5. Recordar resultado
        await self.brain.remember_outcome(
            action="list_product",
            result=listing_result,
        )

        return {
            "decision": decision,
            "listing": listing_result,
            "optimized_product": optimized_product,
        }

    async def _optimize_product_copy(
        self,
        product: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Optimiza título, descripción, precio basado en decisión brain."""

        tactics = decision.get("tactics", {})
        parameters = tactics.get("parameters", {})
        copy_templates = tactics.get("copy", {})

        # Generar título
        title = copy_templates.get("title_template", product.get("name"))

        # Generar descripción
        description_structure = copy_templates.get("structure", [])
        description = await self._build_description(product, description_structure)

        # Calcular precio
        price = parameters.get("recommended_price", product.get("price"))

        return {
            "name": product.get("name"),
            "title": title,
            "description": description,
            "price": price,
            "category": product.get("category"),
            "images": product.get("images", []),
            "strategy": decision.get("strategy"),
        }

    async def _build_description(self, product: Dict[str, Any], structure: List[str]) -> str:
        """Construye descripción siguiendo estructura."""
        parts = []

        # Hook
        parts.append(f"🎯 {product.get('headline', 'Discover the perfect solution for you')}")

        # Problem
        parts.append(f"❌ Tired of: {product.get('problem', 'dealing with subpar products')}")

        # Solution
        parts.append(f"✅ Our {product.get('category', 'product')}: {product.get('value_prop', 'delivers exceptional quality')}")

        # Features
        if product.get("features"):
            parts.append("📋 Key features:")
            for feature in product.get("features", [])[:5]:
                parts.append(f"  • {feature}")

        # Proof
        parts.append(f"⭐ {product.get('rating', '4.9')}/5 stars from {product.get('reviews', '100+')} satisfied customers")

        # CTA
        parts.append("🚀 Order now and get guaranteed satisfaction!")

        return "\n".join(parts)

    async def _execute_listing(self, product: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Ejecuta listing via Computer Use."""

        if platform == "mercadolibre":
            actions = await self._build_ml_listing_actions(product)
        elif platform == "amazon":
            actions = await self._build_amazon_listing_actions(product)
        elif platform == "shopify":
            actions = await self._build_shopify_listing_actions(product)
        elif platform == "tiktok_shop":
            actions = await self._build_tiktok_listing_actions(product)
        else:
            return {"status": "error", "message": f"Platform {platform} not supported"}

        # Ejecutar workflow
        result = await self.browser.execute_workflow(f"intelligent_list_{product.get('id')}", actions)

        return {
            "status": "success" if result.get("completed", 0) > 0 else "partial",
            "actions_completed": result.get("completed", 0),
            "platform": platform,
            "product_id": product.get("id"),
        }

    async def _build_ml_listing_actions(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construye acciones MercadoLibre."""
        return [
            {"type": "navigate", "params": {"url": "https://www.mercadolibre.com.ar/vender"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='titulo']": product.get("title"),
                "input[name='precio']": str(product.get("price")),
                "textarea[name='descripcion']": product.get("description"),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Publicar')"}},
            {"type": "screenshot", "params": {"filename": f"ml_listed_{product.get('id')}.png"}},
        ]

    async def _build_amazon_listing_actions(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"type": "navigate", "params": {"url": "https://sellercentral.amazon.com/products/create"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='title']": product.get("title"),
                "input[name='price']": str(product.get("price")),
                "textarea[name='description']": product.get("description"),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Publish')"}},
        ]

    async def _build_shopify_listing_actions(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"type": "navigate", "params": {"url": "https://admin.shopify.com/products/create"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='title']": product.get("title"),
                "input[name='price']": str(product.get("price")),
                "textarea[name='description']": product.get("description"),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Save')"}},
        ]

    async def _build_tiktok_listing_actions(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"type": "navigate", "params": {"url": "https://seller.tiktok.com/products/add"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='product name']": product.get("title"),
                "input[placeholder*='price']": str(product.get("price")),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Create')"}},
        ]

    # ========== INTELLIGENT NEGOTIATION ==========

    async def intelligent_negotiate(
        self,
        buyer_profile: Dict[str, Any],
        product: Dict[str, Any],
        initial_offer: float,
    ) -> Dict[str, Any]:
        """
        Negocia INTELIGENTEMENTE usando Trump tactics + buyer psychology.

        1. Brain analiza buyer type
        2. Determina leverage points
        3. Ejecuta negoción
        4. Adapta según buyer responses
        """

        logger.info(f"Intelligent negotiation with buyer type: {buyer_profile.get('type')}")

        situation = {
            "platform": "negotiation",
            "action_type": "negotiate_deal",
            "context": {
                "buyer_type": buyer_profile.get("type"),  # price_sensitive, early_adopter, risk_averse
                "product_category": product.get("category"),
                "initial_offer": initial_offer,
                "budget": buyer_profile.get("budget"),
            },
        }

        # Consultar brain
        decision = await self.brain.decide_action(
            situation,
            available_strategies=["aggressive", "consultative", "value_based"],
        )

        tactics = decision.get("tactics", {})
        parameters = tactics.get("parameters", {})

        # Ejecutar negoción
        negotiation_flow = await self._execute_negotiation(
            buyer_profile,
            product,
            decision,
        )

        return {
            "decision": decision,
            "negotiation_flow": negotiation_flow,
            "final_price": negotiation_flow.get("final_price", initial_offer),
        }

    async def _execute_negotiation(
        self,
        buyer_profile: Dict[str, Any],
        product: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ejecuta negociación via Computer Use (WhatsApp, email, etc)."""

        buyer_type = buyer_profile.get("type")
        tactics = decision.get("tactics", {})

        # Mensajes según buyer type
        if buyer_type == "price_sensitive":
            opening_message = f"Tengo {product.get('name')} disponible por ${tactics['parameters'].get('recommended_price', 100)} - es 15% menos que competencia. Te interesa?"
        elif buyer_type == "early_adopter":
            opening_message = f"{product.get('name')} - acceso exclusivo a features premium. Solo disponible para primeros 10 compradores. ¿Quieres reservar?"
        elif buyer_type == "risk_averse":
            opening_message = f"{product.get('name')} con 90-day money-back guarantee. Zero risk. ¿Cuándo te gustaría probarlo?"
        else:
            opening_message = f"Tengo ${product.get('name')} disponible. ¿Cuál es tu mejor precio?"

        # Enviar mensaje via Computer Use (WhatsApp Web)
        actions = [
            {"type": "navigate", "params": {"url": "https://web.whatsapp.com"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='Buscar']": buyer_profile.get("phone", buyer_profile.get("email")),
            }}},
            {"type": "fill_form", "params": {"fields": {
                "div[contenteditable='true']": opening_message,
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Enter"}},
        ]

        result = await self.browser.execute_workflow(
            f"negotiate_{buyer_profile.get('id')}",
            actions,
        )

        # TODO: Esperar respuesta, adaptar según feedback

        return {
            "status": "success" if result.get("completed", 0) > 0 else "failed",
            "opening_price": tactics['parameters'].get('recommended_price', 100),
            "final_price": None,  # TODO: Extraer de buyer response
        }

    # ========== REAL-TIME ADAPTATION ==========

    async def adapt_strategy_realtime(
        self,
        current_performance: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Adapta estrategia en TIEMPO REAL basado en resultados.

        Si CTR bajo → cambia título
        Si conversion bajo → cambia precio o descripción
        Si sentiment negativo → cambia copy
        """

        logger.info("Adapting strategy in real-time based on performance")

        ctr = current_performance.get("ctr", 0)
        conversion_rate = current_performance.get("conversion_rate", 0)
        sentiment_score = current_performance.get("sentiment_score", 0.5)

        recommendations = []

        if ctr < 0.02:  # <2% CTR is bad
            recommendations.append({
                "issue": "Low CTR (interest low)",
                "action": "Change title (more keywords, emotional benefit)",
                "expected_impact": "+50% CTR",
            })

        if conversion_rate < 0.05:  # <5% conversion is bad
            recommendations.append({
                "issue": "Low conversion (buyers hesitant)",
                "action": "Lower price 10% OR add guarantee",
                "expected_impact": "+30% conversion",
            })

        if sentiment_score < 0.5:  # Negative feedback
            recommendations.append({
                "issue": "Negative sentiment from reviews",
                "action": "Address quality issues OR change product positioning",
                "expected_impact": "Sentiment +0.3",
            })

        return {
            "current_performance": current_performance,
            "recommendations": recommendations,
            "should_adapt": len(recommendations) > 0,
        }
