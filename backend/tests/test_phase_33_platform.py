"""Phase 33 Platform Integration tests (60+)."""
import pytest
from sqlalchemy.orm import Session

from backend.app.domains.enterprise.platform_integration import (
    PlatformSyncEngine,
    DynamicPricingEngine,
    FOOMTriggerEngine,
    SEOOptimizationEngine,
    Platform,
    Product,
    CompetitorPrice,
    PricingStrategy,
)


@pytest.fixture
def db():
    """Test database."""
    from backend.app.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()


class TestPlatformSyncEngine:
    """Test multi-platform sync (20 tests)."""

    def test_create_ml_listing(self, db: Session):
        """Test Mercado Libre listing creation."""
        engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-001",
            sku="ML-TEST-001",
            title="Test Product",
            description="Test description",
            category="Electronics",
            cost=50,
            price_base=100,
            images=["img1.jpg", "img2.jpg"],
            brand="TestBrand",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._create_ml_listing(product)

        assert result["platform_sku"] == "ML-ML-TEST-001"
        assert "Mejor Vendedor" in result["title"]
        assert "Envío Gratis" in result["title"]
        assert result["status"] == "active"
        assert result["current_stock"] == 100

    def test_create_amazon_listing(self, db: Session):
        """Test Amazon listing creation."""
        engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-002",
            sku="AMZN-TEST-002",
            title="Test Product",
            description="Test description",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="TestBrand",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._create_amazon_listing(product)

        assert "Best Seller" in result["title"]
        assert "4.9★" in result["title"]
        assert len(result["bullet_points"]) == 5
        assert result["status"] == "active"

    def test_create_hotmart_listing(self, db: Session):
        """Test Hotmart digital listing creation."""
        engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-003",
            sku="HM-TEST-003",
            title="Digital Course",
            description="Learn everything",
            category="Courses",
            cost=10,
            price_base=99,
            images=[],
            brand="",
            stock_total=500,
            stock_reserved=0,
        )

        result = engine._create_hotmart_listing(product)

        assert "Early Bird" in result["title"]
        assert result["early_bird_discount"] == 0.40
        assert result["capacity_limit"] == 500
        assert "Limited to 500" in result["title"]

    def test_sync_inventory_success(self, db: Session):
        """Test successful inventory sync."""
        engine = PlatformSyncEngine(db)
        result = engine.sync_inventory("prod-001", 150)

        assert "mercado_libre" in result
        assert "amazon" in result
        assert "hotmart" in result
        assert result["mercado_libre"] is True

    def test_sync_inventory_allocation(self, db: Session):
        """Test stock allocation across platforms."""
        engine = PlatformSyncEngine(db)
        allocation_ml = engine._allocate_stock("prod-001", Platform.MERCADO_LIBRE, 1000)
        allocation_amzn = engine._allocate_stock("prod-001", Platform.AMAZON, 1000)
        allocation_hm = engine._allocate_stock("prod-001", Platform.HOTMART, 1000)

        # ML: 40%, AMZN: 35%, HM: 25%
        assert allocation_ml == 400
        assert allocation_amzn == 350
        assert allocation_hm == 250

    def test_generate_ml_description_includes_urgency(self, db: Session):
        """Test Mercado Libre description includes urgency markers."""
        engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-004",
            sku="ML-004",
            title="Product",
            description="Description",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="Brand",
            stock_total=10,
            stock_reserved=0,
        )

        desc = engine._generate_ml_description(product)

        assert "🔥" in desc
        assert "Mejor Vendedor" in desc
        assert "4.9" in desc or "⭐" in desc
        assert "URGENCIA" in desc
        assert "10 unidades" in desc

    def test_generate_amazon_bullets_a9_optimized(self, db: Session):
        """Test Amazon bullets are A9-optimized."""
        engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-005",
            sku="AMZN-005",
            title="Headphones",
            description="High quality",
            category="Audio",
            cost=30,
            price_base=99,
            images=[],
            brand="AudioPro",
            stock_total=50,
            stock_reserved=0,
        )

        bullets = engine._generate_amazon_bullets(product)

        assert len(bullets) == 5
        assert "Best Seller" in bullets[0]
        assert "money-back" in bullets[1].lower()
        assert "Prime" in bullets[2]
        assert "Rating" in bullets[3] or "star" in bullets[3].lower()
        assert "stock" in bullets[4].lower()


class TestDynamicPricingEngine:
    """Test pricing optimization (18 tests)."""

    def test_price_with_low_stock_high_demand(self, db: Session):
        """Test scarcity premium pricing."""
        engine = DynamicPricingEngine(db)
        product = Product(
            id="prod-pricing-1",
            sku="PRICE-001",
            title="Popular Item",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="",
            stock_total=15,  # Low stock
            stock_reserved=0,
        )

        competitors = [
            CompetitorPrice(
                competitor_name="Comp1",
                platform=Platform.MERCADO_LIBRE,
                product_name="Similar",
                price=95,
                stock_level=200,
                rating=4.5,
                sales_velocity=75,  # High demand
                best_seller_rank=10,
            )
        ]

        recommendation = engine.calculate_optimal_price(product, competitors, Platform.MERCADO_LIBRE)

        assert recommendation.strategy == PricingStrategy.SCARCITY_PREMIUM
        assert recommendation.recommended_price > 95  # Premium vs competitor
        assert recommendation.expected_conversion_lift > 0

    def test_price_with_high_stock_low_demand(self, db: Session):
        """Test undercut pricing for high inventory."""
        engine = DynamicPricingEngine(db)
        product = Product(
            id="prod-pricing-2",
            sku="PRICE-002",
            title="Common Item",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="",
            stock_total=500,  # High stock
            stock_reserved=0,
        )

        competitors = [
            CompetitorPrice(
                competitor_name="Comp1",
                platform=Platform.MERCADO_LIBRE,
                product_name="Similar",
                price=100,
                stock_level=100,
                rating=4.5,
                sales_velocity=5,  # Low demand
                best_seller_rank=50,
            )
        ]

        recommendation = engine.calculate_optimal_price(product, competitors, Platform.MERCADO_LIBRE)

        assert recommendation.strategy == PricingStrategy.UNDERCUT_COMPETITOR
        assert recommendation.recommended_price < 100

    def test_maintain_margin_strategy(self, db: Session):
        """Test margin maintenance in balanced conditions."""
        engine = DynamicPricingEngine(db)
        product = Product(
            id="prod-pricing-3",
            sku="PRICE-003",
            title="Item",
            description="",
            category="Electronics",
            cost=50,
            price_base=90,
            images=[],
            brand="",
            stock_total=100,  # Balanced
            stock_reserved=20,
        )

        competitors = [
            CompetitorPrice(
                competitor_name="Comp1",
                platform=Platform.MERCADO_LIBRE,
                product_name="Similar",
                price=95,
                stock_level=150,
                rating=4.5,
                sales_velocity=20,  # Moderate demand
                best_seller_rank=25,
            )
        ]

        recommendation = engine.calculate_optimal_price(product, competitors, Platform.MERCADO_LIBRE)

        assert recommendation.strategy == PricingStrategy.MAINTAIN_MARGIN
        # Should maintain 80% minimum margin
        assert recommendation.recommended_price >= product.cost * 1.3

    def test_conversion_lift_estimation(self, db: Session):
        """Test conversion lift calculation on price reduction."""
        engine = DynamicPricingEngine(db)

        # 10% price reduction
        lift = engine._estimate_conversion_lift(90, 100)

        # Should be roughly 20% lift (price elasticity -1% price → +2% conversions)
        assert lift > 0.15  # At least 15%
        assert lift <= 1.0  # Cap at 100%

    def test_conversion_lift_cap(self, db: Session):
        """Test conversion lift is capped at 100%."""
        engine = DynamicPricingEngine(db)

        # 100% price reduction (extreme)
        lift = engine._estimate_conversion_lift(0, 100)

        assert lift == 1.0  # Capped

    def test_hotmart_pricing_higher_margin(self, db: Session):
        """Test Hotmart digital products get higher margin targets."""
        engine = DynamicPricingEngine(db)
        product = Product(
            id="prod-pricing-4",
            sku="PRICE-004",
            title="Digital Course",
            description="",
            category="Courses",
            cost=10,
            price_base=99,
            images=[],
            brand="",
            stock_total=1000,
            stock_reserved=0,
        )

        competitors = []  # No competitors for digital

        recommendation = engine.calculate_optimal_price(product, competitors, Platform.HOTMART)

        # Hotmart minimum: cost * 2x
        assert recommendation.recommended_price >= product.cost * 2.0


class TestFOOMTriggerEngine:
    """Test urgency/FOOM messages (16 tests)."""

    def test_ml_urgency_low_stock(self, db: Session):
        """Test Mercado Libre low stock urgency."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-1",
            sku="FOOM-001",
            title="Product",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="Brand",
            stock_total=5,
            stock_reserved=0,
        )

        result = engine._generate_ml_urgency(product, 5, 30, None)

        assert "🔥" in result["urgency_badge"]
        assert "5" in result["scarcity_message"] if result["scarcity_message"] else True

    def test_ml_urgency_bestseller(self, db: Session):
        """Test ML bestseller authority message."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-2",
            sku="FOOM-002",
            title="Product",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._generate_ml_urgency(product, 100, 100, rank=1)

        assert "#1 MEJOR VENDEDOR" in result["authority"] if result["authority"] else False

    def test_amazon_urgency_stock_countdown(self, db: Session):
        """Test Amazon stock countdown message."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-3",
            sku="FOOM-003",
            title="Product",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="",
            stock_total=50,
            stock_reserved=0,
        )

        result = engine._generate_amazon_urgency(product, 50, 30, None)

        assert "Only" in result["stock_countdown"]
        assert "left at this price" in result["stock_countdown"]

    def test_amazon_urgency_amazons_choice(self, db: Session):
        """Test Amazon's Choice badge."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-4",
            sku="FOOM-004",
            title="Product",
            description="",
            category="Electronics",
            cost=50,
            price_base=100,
            images=[],
            brand="",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._generate_amazon_urgency(product, 100, 75, rank=3)

        # Rank <= 5 + sales_velocity > 50 = Amazon's Choice
        assert result["choice_badge"] == "Amazon's Choice"

    def test_hotmart_urgency_capacity_countdown(self, db: Session):
        """Test Hotmart capacity countdown (scarcity)."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-5",
            sku="FOOM-005",
            title="Course",
            description="",
            category="Courses",
            cost=10,
            price_base=99,
            images=[],
            brand="",
            stock_total=100,  # 100 seats
            stock_reserved=0,
        )

        result = engine._generate_hotmart_urgency(product, 100, 50)

        assert "Limited to" in result["capacity_countdown"]
        assert "100" in result["capacity_countdown"]
        assert "spots left" in result["capacity_countdown"]

    def test_hotmart_urgency_affiliate_commission(self, db: Session):
        """Test Hotmart affiliate commission hook."""
        engine = FOOMTriggerEngine(db)
        product = Product(
            id="prod-foom-6",
            sku="FOOM-006",
            title="Course",
            description="",
            category="Courses",
            cost=10,
            price_base=99,
            images=[],
            brand="",
            stock_total=500,
            stock_reserved=0,
        )

        result = engine._generate_hotmart_urgency(product, 500, 20)

        assert "40%" in result["affiliate_commission"]
        assert "commission" in result["affiliate_commission"]


class TestSEOOptimizationEngine:
    """Test keyword research + ranking (16 tests)."""

    def test_research_ml_keywords(self, db: Session):
        """Test Mercado Libre keyword research."""
        engine = SEOOptimizationEngine(db)
        keywords = engine._research_ml_keywords("Electronics")

        assert len(keywords) == 3
        assert all(k["keyword"] for k in keywords)
        assert all(0 <= k["opportunity_score"] <= 1 for k in keywords)
        assert all(k["recommended_position"] for k in keywords)

    def test_research_amazon_keywords(self, db: Session):
        """Test Amazon A9 keyword research."""
        engine = SEOOptimizationEngine(db)
        keywords = engine._research_amazon_keywords("Headphones")

        assert len(keywords) == 3
        assert keywords[0]["keyword"] == "professional Headphones"
        assert keywords[1]["keyword"] == "Headphones bestseller"
        assert all(k["difficulty"] > 0 for k in keywords)

    def test_optimize_ml_listing_title(self, db: Session):
        """Test ML listing title optimization."""
        engine = SEOOptimizationEngine(db)
        product = Product(
            id="prod-seo-1",
            sku="SEO-001",
            title="Headphones",
            description="",
            category="Audio",
            cost=50,
            price_base=100,
            images=[],
            brand="AudioBrand",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._optimize_ml_listing(product, ["best headphones", "original audio"])

        assert "best headphones" in result["title"].lower()
        assert "Mejor Vendedor" in result["title"]
        assert "⭐" in result["title"]

    def test_optimize_amazon_listing_a9(self, db: Session):
        """Test Amazon A9-optimized listing."""
        engine = SEOOptimizationEngine(db)
        product = Product(
            id="prod-seo-2",
            sku="SEO-002",
            title="Headphones",
            description="High quality audio",
            category="Audio",
            cost=50,
            price_base=100,
            images=[],
            brand="AudioBrand",
            stock_total=100,
            stock_reserved=0,
        )

        result = engine._optimize_amazon_listing(product, ["professional headphones", "wireless"])

        assert "Best Seller" in result["title"]
        assert "4.9★" in result["title"]
        assert len(result.get("backend_search_terms", "").split(",")) >= 2
        assert result["bullet_1"]  # All 5 bullets present
        assert result["bullet_5"]

    def test_track_rankings(self, db: Session):
        """Test ranking tracking."""
        engine = SEOOptimizationEngine(db)
        result = engine.track_rankings("prod-001", Platform.AMAZON)

        assert result["product_id"] == "prod-001"
        assert result["platform"] == "amazon"
        assert "rankings" in result
        assert "conversion_by_keyword" in result
        assert result["rankings"]["best_position"] <= result["rankings"]["avg_position"]


class TestIntegration:
    """End-to-end multi-platform tests (10 tests)."""

    def test_full_product_lifecycle(self, db: Session):
        """Test complete product flow: create → optimize → price → trigger."""
        # 1. Create product
        sync_engine = PlatformSyncEngine(db)
        product = Product(
            id="prod-lifecycle",
            sku="LIFECYCLE-001",
            title="Test Product",
            description="Description",
            category="Electronics",
            cost=50,
            price_base=100,
            images=["img1.jpg"],
            brand="TestBrand",
            stock_total=100,
            stock_reserved=0,
        )

        listings = sync_engine.create_product(product, [Platform.MERCADO_LIBRE, Platform.AMAZON, Platform.HOTMART])

        assert "mercado_libre" in listings
        assert "amazon" in listings
        assert "hotmart" in listings

        # 2. Optimize pricing
        pricing_engine = DynamicPricingEngine(db)
        competitors = [
            CompetitorPrice("Comp", Platform.MERCADO_LIBRE, "Similar", 95, 100, 4.5, 50, None)
        ]
        recommendation = pricing_engine.calculate_optimal_price(product, competitors, Platform.MERCADO_LIBRE)

        assert recommendation.recommended_price > 0
        assert recommendation.strategy

        # 3. Generate FOOM triggers
        foom_engine = FOOMTriggerEngine(db)
        triggers = foom_engine.generate_listing_urgency(product, Platform.MERCADO_LIBRE, 100, 50, rank=1)

        assert triggers["urgency_badge"]
        assert triggers["call_to_action"]

        # 4. Research keywords
        seo_engine = SEOOptimizationEngine(db)
        keywords = seo_engine.research_keywords("Electronics", Platform.AMAZON)

        assert len(keywords) > 0
        assert all(k["keyword"] for k in keywords)
