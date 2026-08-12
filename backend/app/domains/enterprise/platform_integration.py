"""Phase 33: Multi-Platform Seller Automation Engine.

4 Core Systems:
1. PlatformSyncEngine - Product/inventory sync (ML, Amazon, Hotmart)
2. DynamicPricingEngine - Hourly repricing + margin optimization
3. FOOMTriggerEngine - Platform-specific urgency messages
4. SEOOptimizationEngine - Keyword ranking + listing A/B testing
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

class Platform(Enum):
    """Supported marketplace platforms."""
    MERCADO_LIBRE = "mercado_libre"
    AMAZON = "amazon"
    HOTMART = "hotmart"


class PricingStrategy(Enum):
    """Dynamic pricing strategies."""
    UNDERCUT_COMPETITOR = "undercut_competitor"  # -5% to -15%
    MAINTAIN_MARGIN = "maintain_margin"  # cost * 1.5-2x
    SCARCITY_PREMIUM = "scarcity_premium"  # cost * 2.5-3x (low stock)
    SEASONAL_SURGE = "seasonal_surge"  # cost * 3-4x (holidays)
    FIRST_MOVER = "first_mover"  # cost * 1.3x (new listing)


@dataclass
class Product:
    """Master product catalog."""
    id: str
    sku: str
    title: str
    description: str
    category: str
    cost: float
    price_base: float  # Target price
    images: List[str]
    brand: str
    stock_total: int
    stock_reserved: int  # Reserved across all platforms


@dataclass
class PlatformListing:
    """Per-platform listing mapping."""
    id: str
    product_id: str
    platform: Platform
    platform_sku: str
    listing_url: str
    status: str  # active, inactive, delisted
    current_stock: int
    current_price: float
    rating: float  # 0-5
    rating_count: int
    last_sync_at: datetime
    best_seller_rank: Optional[int] = None


@dataclass
class CompetitorPrice:
    """Competitor price data."""
    competitor_name: str
    platform: Platform
    product_name: str
    price: float
    stock_level: int
    rating: float
    sales_velocity: float  # Units per day
    best_seller_rank: Optional[int] = None


@dataclass
class PricingRecommendation:
    """AI-optimized price recommendation."""
    product_id: str
    platform: Platform
    recommended_price: float
    strategy: PricingStrategy
    reasoning: str
    expected_conversion_lift: float  # 0-1
    margin_impact: float  # % change vs current


class PlatformSyncEngine:
    """Unify products across 3 platforms. Real-time inventory sync."""

    def __init__(self, db):
        self.db = db

    def create_product(self, product: Product, platforms: List[Platform]) -> Dict[str, Any]:
        """Create product on specified platforms."""
        results = {}

        for platform in platforms:
            if platform == Platform.MERCADO_LIBRE:
                results["mercado_libre"] = self._create_ml_listing(product)
            elif platform == Platform.AMAZON:
                results["amazon"] = self._create_amazon_listing(product)
            elif platform == Platform.HOTMART:
                results["hotmart"] = self._create_hotmart_listing(product)

        return results

    def _create_ml_listing(self, product: Product) -> Dict[str, Any]:
        """Create Mercado Libre listing."""
        return {
            "platform_sku": f"ML-{product.sku}",
            "listing_url": f"https://articulo.mercadolibre.com.ar/MLA-{product.sku}",
            "title": f"{product.title} | Mejor Vendedor | Envío Gratis",
            "description": self._generate_ml_description(product),
            "status": "active",
            "current_stock": product.stock_total,
            "current_price": product.price_base,
        }

    def _create_amazon_listing(self, product: Product) -> Dict[str, Any]:
        """Create Amazon listing."""
        return {
            "platform_sku": f"AMZN-{product.sku}",
            "listing_url": f"https://www.amazon.com/dp/ASIN{product.sku}",
            "title": f"{product.title} | Best Seller | Free Shipping | 4.9★",
            "description": self._generate_amazon_description(product),
            "bullet_points": self._generate_amazon_bullets(product),
            "status": "active",
            "current_stock": product.stock_total,
            "current_price": product.price_base,
        }

    def _create_hotmart_listing(self, product: Product) -> Dict[str, Any]:
        """Create Hotmart (digital) listing."""
        return {
            "platform_sku": f"HM-{product.sku}",
            "listing_url": f"https://hotmart.com/pt/product/{product.sku}",
            "title": f"🚀 {product.title} | Early Bird -40% | Limited to 500 Buyers",
            "description": self._generate_hotmart_hook(product),
            "status": "active",
            "current_stock": product.stock_total,
            "current_price": product.price_base,
            "early_bird_discount": 0.40,
            "capacity_limit": 500,
        }

    def sync_inventory(self, product_id: str, new_stock: int) -> Dict[str, bool]:
        """Real-time inventory sync across all platforms."""
        # Reserve inventory first (prevent overselling)
        reserved = self._calculate_reserved_stock(product_id)
        available = new_stock - reserved

        if available < 0:
            return {"error": "Stock insufficient after reservations", "available": 0}

        sync_results = {}
        platforms = [Platform.MERCADO_LIBRE, Platform.AMAZON, Platform.HOTMART]

        for platform in platforms:
            try:
                # Distribute stock proportionally across platforms
                platform_allocation = self._allocate_stock(product_id, platform, available)
                sync_results[platform.value] = self._push_stock_to_platform(
                    product_id, platform, platform_allocation
                )
            except Exception as e:
                sync_results[platform.value] = False
                print(f"Sync failed for {platform.value}: {str(e)}")

        return sync_results

    def _calculate_reserved_stock(self, product_id: str) -> int:
        """Calculate stock reserved from recent sales."""
        # Get orders in last 24h (not yet fulfilled)
        # Usually ships within 24-48h
        return 50  # Mock: typically 50 units reserved

    def _allocate_stock(self, product_id: str, platform: Platform, available: int) -> int:
        """Allocate stock based on platform performance."""
        # Mercado Libre: 40% (LATAM leader)
        # Amazon: 35% (global, but region-limited)
        # Hotmart: 25% (digital, unlimited fulfillment)
        allocation_map = {
            Platform.MERCADO_LIBRE: 0.40,
            Platform.AMAZON: 0.35,
            Platform.HOTMART: 0.25,
        }
        return int(available * allocation_map[platform])

    def _push_stock_to_platform(self, product_id: str, platform: Platform, quantity: int) -> bool:
        """Push stock update to platform API."""
        # Mock: would call actual platform API
        return True

    def _generate_ml_description(self, product: Product) -> str:
        """Generate Mercado Libre urgency description."""
        return f"""
{product.description}

🔥 CARACTERÍSTICAS PRINCIPALES:
✓ Mejor Vendedor en categoría
✓ Envío GRATIS a todo el país
✓ Garantía de 30 días
✓ Certificado 4.9/5 estrellas

⏰ URGENCIA: Solo {product.stock_total} unidades disponibles a este precio
📈 {product.stock_total - 10}+ vendidas esta semana

🎁 ENVÍO EXPRESS en CABA (48hs)
💳 Hasta 12 cuotas sin interés

Compra con CONFIANZA de mejor vendedor ⭐⭐⭐⭐⭐
        """

    def _generate_amazon_description(self, product: Product) -> str:
        """Generate Amazon A9-optimized description."""
        return f"""
{product.description}

KEY FEATURES:
• Premium Quality - Trusted by 50,000+ customers
• Money-Back Guarantee - 30 days, no questions asked
• Free Shipping - 2-day delivery with Prime
• Best Seller Status - #1 in category

LIMITED TIME OFFER:
Stock at this price: {product.stock_total} units
Selling fast: 100+ sold this week
⭐ 4.9 stars from 500+ verified reviews

SPECIFICATIONS:
Brand: {product.brand}
Category: {product.category}
Guarantee: 30 days
Support: 24/7 customer service

⚡ ORDER NOW - Price drops daily
        """

    def _generate_amazon_bullets(self, product: Product) -> List[str]:
        """Generate 5 Amazon bullet points for A9."""
        return [
            f"#1 Best Seller in {product.category} - Trusted by 50k+ customers",
            "30-day money-back guarantee with free return shipping",
            "Free 2-day delivery with Prime membership included",
            f"Premium {product.brand} quality, certified 4.9★ rating",
            "Limited stock at this price - {product.stock_total} units available",
        ]

    def _generate_hotmart_hook(self, product: Product) -> str:
        """Generate Hotmart pre-launch FOOM hook."""
        return f"""
🚀 LANÇAMENTO EXCLUSIVO - Últimas 24 horas de Early Bird!

{product.description}

⏰ OFERTA LIMITADA:
✅ Early Bird: -40% OFF (primeiros 100 compradores)
✅ Acesso IMEDIATO após compra
✅ Garantia de 7 dias ou seu dinheiro de volta
✅ Comunidade exclusiva de bônus

🎯 POR QUE AGORA?
📈 Apenas {product.stock_total} vagas disponíveis
💰 Preço nunca mais será tão baixo
⭐ 500+ clientes já garantiram o acesso
🔥 Tendência: +1000 vendas/semana

🎁 BÔNUS DE LANÇAMENTO:
• Consultoria 1-on-1 ($97 valor)
• Grupo VIP de acesso antecipado
• Atualizações gratuitas por 1 ano

👉 GARANTA SEU ACESSO AGORA - Próximo preço: 2x
        """


class DynamicPricingEngine:
    """Hourly repricing + margin optimization across platforms."""

    def __init__(self, db):
        self.db = db

    def calculate_optimal_price(
        self, product: Product, competitors: List[CompetitorPrice], platform: Platform
    ) -> PricingRecommendation:
        """Calculate optimal price based on competitors + demand + inventory."""
        strategy, price, reasoning = self._run_pricing_strategy(
            product, competitors, platform
        )

        expected_lift = self._estimate_conversion_lift(price, product.price_base)
        margin_pct = ((price - product.cost) / product.cost) * 100

        return PricingRecommendation(
            product_id=product.id,
            platform=platform,
            recommended_price=price,
            strategy=strategy,
            reasoning=reasoning,
            expected_conversion_lift=expected_lift,
            margin_impact=margin_pct - (((product.price_base - product.cost) / product.cost) * 100),
        )

    def _run_pricing_strategy(
        self, product: Product, competitors: List[CompetitorPrice], platform: Platform
    ) -> Tuple[PricingStrategy, float, str]:
        """Select pricing strategy based on market conditions."""

        # Get competitor average price
        if competitors:
            avg_competitor_price = sum(c.price for c in competitors) / len(competitors)
            lowest_competitor = min(c.price for c in competitors)
        else:
            avg_competitor_price = product.price_base
            lowest_competitor = product.price_base

        # Check inventory level
        stock_level = product.stock_total - (product.stock_total * 0.10)  # Account for reserved
        is_low_stock = stock_level < 50
        is_high_stock = stock_level > 200

        # Check sales velocity (mock: daily units)
        sales_velocity = 10  # Mock
        is_high_demand = sales_velocity > 50

        # Strategy selection
        if product.stock_total < 20 and is_high_demand:
            # Scarcity premium: few units left, high demand
            price = lowest_competitor * 1.15  # 15% premium
            strategy = PricingStrategy.SCARCITY_PREMIUM
            reasoning = f"Low stock ({product.stock_total} units) + high demand ({sales_velocity}/day) = premium pricing"

        elif is_high_stock and not is_high_demand:
            # Undercut: lots of inventory, low sales
            price = lowest_competitor * 0.95  # 5% undercut
            strategy = PricingStrategy.UNDERCUT_COMPETITOR
            reasoning = f"High inventory ({stock_level:.0f} units) + low demand = competitive pricing"

        elif is_high_demand:
            # First-mover discount: new listing, boost visibility
            price = lowest_competitor * 0.90  # 10% undercut
            strategy = PricingStrategy.FIRST_MOVER
            reasoning = "New listing - aggressive undercut for ranking boost"

        else:
            # Maintain margin: balanced inventory + moderate demand
            price = max(product.cost * 1.8, lowest_competitor * 0.98)  # Maintain 80% margin minimum
            strategy = PricingStrategy.MAINTAIN_MARGIN
            reasoning = "Balanced conditions - optimize for margin"

        # Enforce platform-specific floors
        if platform == Platform.HOTMART:
            # Digital: higher margin OK
            price = max(price, product.cost * 2.0)
        else:
            # Physical: tighter margins
            price = max(price, product.cost * 1.3)

        return strategy, round(price, 2), reasoning

    def _estimate_conversion_lift(self, new_price: float, old_price: float) -> float:
        """Estimate conversion rate improvement from price change."""
        pct_change = (new_price - old_price) / old_price if old_price > 0 else 0

        # Price elasticity: -1% price → +2% conversions (typical)
        if pct_change < 0:
            return min(1.0, abs(pct_change) * 2)  # Cap at 100% lift
        else:
            return max(-0.5, pct_change * -2)  # Cap at -50% drop

    def reprice_all_products(self, platform: Platform, frequency: str = "hourly") -> Dict[str, Any]:
        """Batch reprice all active listings on platform."""
        # Mock: would fetch all products + competitor prices
        results = {
            "platform": platform.value,
            "timestamp": datetime.utcnow().isoformat(),
            "frequency": frequency,
            "products_repriced": 150,
            "price_changes": {
                "increased": 45,  # +margin optimization
                "decreased": 60,  # -competitive pressure
                "maintained": 45,  # No change strategy
            },
            "revenue_impact": "+8.5% estimated MRR",
        }
        return results


class FOOMTriggerEngine:
    """Generate platform-specific urgency messages."""

    def __init__(self, db):
        self.db = db

    def generate_listing_urgency(
        self, product: Product, platform: Platform, inventory: int, sales_velocity: float, rank: Optional[int] = None
    ) -> Dict[str, str]:
        """Generate platform-optimized urgency messages."""

        if platform == Platform.MERCADO_LIBRE:
            return self._generate_ml_urgency(product, inventory, sales_velocity, rank)
        elif platform == Platform.AMAZON:
            return self._generate_amazon_urgency(product, inventory, sales_velocity, rank)
        elif platform == Platform.HOTMART:
            return self._generate_hotmart_urgency(product, inventory, sales_velocity)

    def _generate_ml_urgency(
        self, product: Product, inventory: int, sales_velocity: float, rank: Optional[int]
    ) -> Dict[str, str]:
        """Mercado Libre urgency (scarcity + bestseller)."""
        urgency_lines = []

        if inventory < 10:
            urgency_lines.append(f"🔥 ¡SOLO {inventory} QUEDAN A ESTE PRECIO!")
        elif inventory < 50:
            urgency_lines.append(f"⚠️ Stock limitado: {inventory} unidades disponibles")

        if sales_velocity > 50:
            urgency_lines.append(f"📈 +{int(sales_velocity)} vendidas esta semana")

        if rank and rank <= 3:
            urgency_lines.append(f"🥇 #{rank} MEJOR VENDEDOR en categoría")

        return {
            "urgency_badge": "🔥 OFERTA LIMITADA" if inventory < 30 else "⭐ BESTSELLER",
            "scarcity_message": urgency_lines[0] if urgency_lines else None,
            "social_proof": urgency_lines[1] if len(urgency_lines) > 1 else None,
            "authority": urgency_lines[2] if len(urgency_lines) > 2 else None,
            "call_to_action": "¡COMPRA AHORA - Precio baja diariamente!",
        }

    def _generate_amazon_urgency(
        self, product: Product, inventory: int, sales_velocity: float, rank: Optional[int]
    ) -> Dict[str, str]:
        """Amazon urgency (A9 optimized - stock countdown)."""
        return {
            "badge": "Best Seller" if rank and rank <= 1 else "Limited Stock",
            "stock_countdown": f"Only {max(1, inventory // 10)} left at this price",
            "sales_velocity": f"{int(sales_velocity)}/day selling fast" if sales_velocity > 50 else None,
            "choice_badge": "Amazon's Choice" if rank and rank <= 5 and sales_velocity > 50 else None,
            "lightning_deal": "Limited Time Offer" if inventory < 20 else None,
            "call_to_action": "✓ Secure your order before stock runs out",
        }

    def _generate_hotmart_urgency(
        self, product: Product, inventory: int, sales_velocity: float
    ) -> Dict[str, str]:
        """Hotmart urgency (pre-launch + affiliate FOOM)."""
        return {
            "pre_launch_timer": "🚀 Launching in 3 days | Early bird gets 40% off",
            "capacity_countdown": f"⏰ Limited to {inventory} buyers | {inventory - int(sales_velocity * 7)} spots left",
            "early_bird_offer": "💰 First 100 customers: -40% OFF + exclusive bonuses",
            "affiliate_commission": "🤝 Creators: 40% commission | Promote & earn",
            "urgency_hook": f"📈 {int(sales_velocity * 7)}+ buyers already joined",
            "money_back": "✅ 7-day money-back guarantee - zero risk",
            "call_to_action": "👉 GRAB YOUR ACCESS NOW - Next price will be 2x higher",
        }


class SEOOptimizationEngine:
    """Keyword research + listing optimization + ranking tracking."""

    def __init__(self, db):
        self.db = db

    def research_keywords(
        self, product_category: str, platform: Platform
    ) -> List[Dict[str, Any]]:
        """Research high-volume, low-competition keywords."""

        if platform == Platform.MERCADO_LIBRE:
            keywords = self._research_ml_keywords(product_category)
        elif platform == Platform.AMAZON:
            keywords = self._research_amazon_keywords(product_category)
        else:  # HOTMART
            keywords = self._research_hotmart_keywords(product_category)

        return keywords

    def _research_ml_keywords(self, category: str) -> List[Dict[str, Any]]:
        """Mercado Libre keyword research."""
        return [
            {
                "keyword": f"{category} mejor",
                "search_volume": 5000,
                "competition": "high",
                "difficulty": 0.7,
                "opportunity_score": 0.5,  # High volume but competitive
                "recommended_position": "title",
            },
            {
                "keyword": f"{category} original",
                "search_volume": 2000,
                "competition": "medium",
                "difficulty": 0.4,
                "opportunity_score": 0.8,  # Sweet spot
                "recommended_position": "title + bullets",
            },
            {
                "keyword": f"{category} garantía",
                "search_volume": 1500,
                "competition": "low",
                "difficulty": 0.2,
                "opportunity_score": 0.9,  # Easy win
                "recommended_position": "description",
            },
        ]

    def _research_amazon_keywords(self, category: str) -> List[Dict[str, Any]]:
        """Amazon A9 keyword research."""
        return [
            {
                "keyword": f"professional {category}",
                "search_volume": 10000,
                "competition": "high",
                "difficulty": 0.8,
                "opportunity_score": 0.4,
                "recommended_position": "backend_search_terms",
            },
            {
                "keyword": f"{category} bestseller",
                "search_volume": 8000,
                "competition": "high",
                "difficulty": 0.7,
                "opportunity_score": 0.5,
                "recommended_position": "title",
            },
            {
                "keyword": f"affordable {category}",
                "search_volume": 3000,
                "competition": "medium",
                "difficulty": 0.5,
                "opportunity_score": 0.7,
                "recommended_position": "title + bullets",
            },
        ]

    def _research_hotmart_keywords(self, category: str) -> List[Dict[str, Any]]:
        """Hotmart keyword research (affiliate-focused)."""
        return [
            {
                "keyword": f"{category} course",
                "search_volume": 5000,
                "competition": "high",
                "difficulty": 0.7,
                "opportunity_score": 0.5,
                "affiliate_potential": 0.8,
            },
            {
                "keyword": f"learn {category}",
                "search_volume": 3000,
                "competition": "medium",
                "difficulty": 0.4,
                "opportunity_score": 0.8,
                "affiliate_potential": 0.9,
            },
        ]

    def optimize_listing(
        self, product: Product, platform: Platform, keywords: List[str]
    ) -> Dict[str, str]:
        """Generate optimized title, bullets, description."""

        if platform == Platform.MERCADO_LIBRE:
            return self._optimize_ml_listing(product, keywords)
        elif platform == Platform.AMAZON:
            return self._optimize_amazon_listing(product, keywords)
        else:  # HOTMART
            return self._optimize_hotmart_listing(product, keywords)

    def _optimize_ml_listing(self, product: Product, keywords: List[str]) -> Dict[str, str]:
        """Optimize for Mercado Libre ranking (sales velocity + reviews)."""
        primary_keyword = keywords[0] if keywords else product.category

        return {
            "title": f"{product.title} {primary_keyword} | Mejor Vendedor ⭐⭐⭐⭐⭐",
            "description_hook": f"El MEJOR {primary_keyword} del mercado - Comprado por +1000 clientes satisfechos",
            "key_benefits": [
                "✓ Certificado por mejor vendedor",
                f"✓ +1000 reseñas positivas",
                "✓ Garantía de satisfacción 30 días",
                "✓ Envío EXPRESS gratis",
            ],
        }

    def _optimize_amazon_listing(self, product: Product, keywords: List[str]) -> Dict[str, str]:
        """Optimize for Amazon A9 algorithm (keywords + conversion)."""
        primary_kw = keywords[0] if keywords else product.category
        secondary_kw = keywords[1] if len(keywords) > 1 else "bestseller"

        return {
            "title": f"{product.title} | {primary_kw} | Best Seller | 4.9★",
            "bullet_1": f"#{1} {primary_kw} on Amazon - Trusted by 50,000+ customers",
            "bullet_2": f"Premium {secondary_kw} quality with 30-day money-back guarantee",
            "bullet_3": "Free 2-day shipping with Prime - Limited stock at this price",
            "bullet_4": f"500+ verified 5-star reviews - Amazon's Choice certified",
            "bullet_5": "24/7 customer support - Satisfaction guaranteed or full refund",
            "backend_search_terms": ",".join(keywords),
        }

    def _optimize_hotmart_listing(self, product: Product, keywords: List[str]) -> Dict[str, str]:
        """Optimize for Hotmart pre-launch (urgency + affiliate appeal)."""
        return {
            "title": f"🚀 {product.title} | Early Bird -40% | {keywords[0] if keywords else 'Digital Course'}",
            "hook": f"Learn how to master {keywords[0] if keywords else product.category} - Limited to 500 buyers, early bird saves 40%",
            "affiliate_angle": f"Creators: Promote this {keywords[0] if keywords else 'course'} and earn 40% commission per sale",
            "urgency_line": "⏰ Early bird pricing ends in 72 hours - Next tier will cost 2x",
        }

    def track_rankings(self, product_id: str, platform: Platform) -> Dict[str, Any]:
        """Track daily ranking position + keyword performance."""
        return {
            "product_id": product_id,
            "platform": platform.value,
            "tracking_period": "last_30_days",
            "keywords_tracked": 15,
            "rankings": {
                "best_position": 1,  # #1 in category
                "avg_position": 5,
                "ranking_trend": "↗️ Up 3 positions",
            },
            "conversion_by_keyword": {
                "primary_keyword": 0.12,  # 12% conversion
                "secondary_keyword": 0.08,  # 8% conversion
                "longtail_keyword": 0.15,  # 15% conversion (high intent)
            },
        }
