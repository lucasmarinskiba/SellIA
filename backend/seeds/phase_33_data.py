"""Phase 33 Seed Data - Real numbers for development/demo."""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

try:
    from backend.app.models.platform_integration import (
        Product,
        PlatformListing,
        PriceHistory,
        CompetitorPrice,
        KeywordResearch,
        ListingVersion,
        CustomerReview,
        Order,
        SellerMetrics,
    )
except ImportError:
    # Fallback if imports fail
    pass


def seed_phase_33_data(db: Session):
    """Populate Phase 33 with realistic data."""

    seller_id = "seller-sellbot-001"

    # ===== PRODUCTS =====
    products = [
        Product(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sku="HDP-PRO-001",
            title="Premium Wireless Headphones Pro",
            description="High-quality wireless headphones with noise cancellation",
            category="Audio",
            cost=45.0,
            price_base=99.99,
            images=["img1.jpg", "img2.jpg"],
            brand="AudioPro",
            stock_total=250,
            stock_reserved=45,
            is_digital=False,
            created_at=datetime.utcnow() - timedelta(days=60),
        ),
        Product(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sku="CHG-FAST-002",
            title="Fast Wireless Charging Pad",
            description="15W wireless charging pad for phones",
            category="Accessories",
            cost=18.0,
            price_base=49.99,
            images=["img1.jpg"],
            brand="ChargePro",
            stock_total=500,
            stock_reserved=120,
            is_digital=False,
            created_at=datetime.utcnow() - timedelta(days=45),
        ),
        Product(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sku="USB-CABLE-003",
            title="USB-C Fast Data Cable",
            description="Premium USB-C cable for fast charging and data transfer",
            category="Cables",
            cost=3.0,
            price_base=12.99,
            images=["img1.jpg"],
            brand="DataLink",
            stock_total=2000,
            stock_reserved=300,
            is_digital=False,
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
        Product(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sku="COURSE-AI-001",
            title="Complete AI Automation Masterclass",
            description="Learn AI automation with Python and GPT APIs",
            category="Courses",
            cost=5.0,
            price_base=99.99,
            images=[],
            brand="SellIA Academy",
            stock_total=500,
            stock_reserved=0,
            is_digital=True,
            created_at=datetime.utcnow() - timedelta(days=15),
        ),
    ]

    for product in products:
        db.add(product)

    db.commit()

    # ===== PLATFORM LISTINGS =====
    product_ids = [p.id for p in products]

    listings_data = [
        # Product 1: Headphones
        (product_ids[0], "mercado_libre", "MLA-12345678", 8.2, 425, 64),
        (product_ids[0], "amazon", "B09X1Y2Z3A", 8.0, 380, 52),
        (product_ids[0], "hotmart", "HM-12345678", 8.4, 250, 38),
        # Product 2: Charger
        (product_ids[1], "mercado_libre", "MLA-87654321", 7.8, 310, 45),
        (product_ids[1], "amazon", "B09X2Y3Z4B", 7.6, 280, 38),
        (product_ids[1], "hotmart", "HM-87654321", 8.1, 180, 28),
        # Product 3: Cable
        (product_ids[2], "mercado_libre", "MLA-11223344", 7.5, 1200, 68),
        (product_ids[2], "amazon", "B09X3Y4Z5C", 7.4, 950, 55),
        # Product 4: Course
        (product_ids[3], "hotmart", "HM-11223344", 9.2, 350, 85),
    ]

    for product_id, platform, platform_sku, rating, sales_month, count in listings_data:
        listing = PlatformListing(
            id=uuid.uuid4(),
            product_id=product_id,
            platform=platform,
            platform_sku=platform_sku,
            listing_url=f"https://{platform}.com/{platform_sku}",
            status="active",
            current_stock=500 if platform != "hotmart" else 350,
            current_price=99.99 if "Headphones" in products[product_ids.index(product_id)].title else 49.99,
            rating=rating,
            rating_count=count,
            sales_this_month=sales_month,
            best_seller_rank=1 if sales_month > 300 else (3 if sales_month > 200 else 5),
            last_sync_at=datetime.utcnow(),
        )
        db.add(listing)

    db.commit()

    listing_ids = db.query(PlatformListing).all()

    # ===== PRICE HISTORY =====
    for listing in listing_ids[:3]:
        prices = [
            (99.99, 99.99, "first_mover"),
            (99.99, 94.99, "undercut_competitor"),
            (94.99, 94.99, "maintain_margin"),
            (94.99, 89.99, "undercut_competitor"),
        ]
        for old_p, new_p, strategy in prices:
            db.add(
                PriceHistory(
                    id=uuid.uuid4(),
                    listing_id=listing.id,
                    old_price=old_p,
                    new_price=new_p,
                    strategy=strategy,
                    reason="Competitive repricing",
                    competitor_price=new_p + 5,
                    inventory_level=listing.current_stock,
                    timestamp=datetime.utcnow(),
                )
            )

    db.commit()

    # ===== COMPETITOR PRICES =====
    for product in products[:3]:
        competitors = [
            ("CompetitorA", 95.99, 200, 8.1),
            ("CompetitorB", 104.99, 150, 7.9),
            ("CompetitorC", 99.99, 100, 8.2),
        ]
        for comp_name, price, stock, rating in competitors:
            db.add(
                CompetitorPrice(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    platform="mercado_libre",
                    competitor_name=comp_name,
                    competitor_sku=f"SKU-{comp_name}",
                    price=price,
                    stock_level=stock,
                    rating=rating,
                    sales_velocity=stock / 15,  # Units per day
                    best_seller_rank=2 if rating > 8.0 else 5,
                    last_checked=datetime.utcnow(),
                )
            )

    db.commit()

    # ===== KEYWORDS =====
    keywords_data = [
        ("wireless headphones", 3000, 1, "medium", 0.90, 0.12),
        ("best headphones", 5000, 3, "high", 0.60, 0.08),
        ("affordable headphones", 2000, 2, "low", 0.95, 0.15),
        ("professional headphones", 1500, 5, "high", 0.40, 0.20),
    ]

    for keyword, vol, rank, comp, opp, conv_rate in keywords_data:
        db.add(
            KeywordResearch(
                id=uuid.uuid4(),
                product_id=product_ids[0],
                platform="amazon",
                keyword=keyword,
                search_volume=vol,
                competition=comp,
                difficulty=0.7 if comp == "high" else (0.5 if comp == "medium" else 0.2),
                opportunity_score=opp,
                current_rank=rank,
                rank_trend="up" if rank < 3 else ("stable" if rank < 5 else "down"),
                conversion_rate=conv_rate,
            )
        )

    db.commit()

    # ===== LISTING VERSIONS =====
    for listing in listing_ids[:3]:
        versions = [
            ("Headphones | Premium Quality", 1200, 96, 0.08, 8.0),
            ("Best Seller Headphones | Free Shipping | 4.9★", 1500, 180, 0.12, 8.2),
            ("Professional Wireless Headphones | Bestseller", 800, 120, 0.15, 8.4),
        ]
        for idx, (title, impr, conv, conv_rate, rating) in enumerate(versions, 1):
            db.add(
                ListingVersion(
                    id=uuid.uuid4(),
                    listing_id=listing.id,
                    version_num=idx,
                    title=title,
                    description="High quality audio product",
                    bullet_points=["Feature 1", "Feature 2", "Feature 3"],
                    keywords=["headphones", "wireless", "best"],
                    a_b_test_group="control" if idx == 1 else ("treatment" if idx == 2 else "treatment_b"),
                    is_active=True,
                    conversions=conv,
                    impressions=impr,
                    conversion_rate=conv_rate,
                    avg_rating=rating,
                    created_at=datetime.utcnow() - timedelta(days=30 - idx * 10),
                    activated_at=datetime.utcnow() - timedelta(days=30 - idx * 10),
                )
            )

    db.commit()

    # ===== CUSTOMER REVIEWS =====
    for listing in listing_ids:
        reviews_data = [
            ("user123", 5, "Excellent product, very satisfied!"),
            ("user456", 5, "Amazing quality and fast shipping"),
            ("user789", 4, "Good product, as described"),
            ("user000", 5, "Highly recommend!"),
            ("user111", 4, "Good value for money"),
        ]
        for user, rating, text in reviews_data:
            db.add(
                CustomerReview(
                    id=uuid.uuid4(),
                    listing_id=listing.id,
                    platform=listing.platform,
                    platform_review_id=f"REV-{user}",
                    reviewer_name=user,
                    rating=rating,
                    review_text=text,
                    is_flagged=False,
                    seller_response="Thank you for your feedback!",
                    response_date=datetime.utcnow(),
                    helpful_count=5 if rating == 5 else 2,
                    created_at=datetime.utcnow() - timedelta(days=10),
                )
            )

    db.commit()

    # ===== ORDERS =====
    for listing in listing_ids:
        for i in range(25):  # 25 orders per listing
            db.add(
                Order(
                    id=uuid.uuid4(),
                    platform=listing.platform,
                    platform_order_id=f"ORD-{listing.platform_sku}-{i}",
                    listing_id=listing.id,
                    product_id=listing.product_id,
                    buyer_id=f"buyer-{i}",
                    price=listing.current_price,
                    quantity=1,
                    order_status="delivered",
                    created_at=datetime.utcnow() - timedelta(days=30 - i),
                    shipped_at=datetime.utcnow() - timedelta(days=28 - i),
                    delivered_at=datetime.utcnow() - timedelta(days=25 - i),
                )
            )

    db.commit()

    # ===== SELLER METRICS =====
    for platform in ["mercado_libre", "amazon", "hotmart"]:
        db.add(
            SellerMetrics(
                id=uuid.uuid4(),
                seller_id=seller_id,
                platform=platform,
                metric_date=datetime.utcnow().date(),
                active_listings=150 if platform == "mercado_libre" else (120 if platform == "amazon" else 80),
                bestseller_count=8 if platform == "mercado_libre" else (3 if platform == "amazon" else 1),
                top_5_count=25 if platform == "mercado_libre" else (15 if platform == "amazon" else 5),
                avg_rating=4.8 if platform == "mercado_libre" else (4.7 if platform == "amazon" else 4.9),
                total_reviews=500 if platform == "mercado_libre" else (400 if platform == "amazon" else 200),
                daily_orders=50 if platform == "mercado_libre" else (40 if platform == "amazon" else 30),
                daily_gmv=8000 if platform == "mercado_libre" else (6000 if platform == "amazon" else 4000),
                conversion_rate=0.12 if platform == "mercado_libre" else (0.10 if platform == "amazon" else 0.15),
                return_rate=0.02,
            )
        )

    db.commit()

    print("✅ Phase 33 seed data loaded successfully!")
    print(f"  - {len(products)} products")
    print(f"  - {len(listing_ids)} platform listings")
    print(f"  - Orders, reviews, metrics populated")
