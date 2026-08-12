"""Phase 33 seed data initialization.

Auto-runs on backend startup if tables are empty.
Professional approach: SQLAlchemy + declarative models.
"""

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

# Import models
from backend.app.models.platform_integration import (
    Product,
    PlatformListing,
    CustomerReview,
    Order,
    SellerMetrics,
)


def seed_phase_33(db: Session) -> dict:
    """Load Phase 33 seed data (real numbers for demo/dev)."""

    # Check if data already loaded
    existing = db.query(Product).first()
    if existing:
        return {"status": "skipped", "reason": "Data already exists"}

    try:
        # ===== PRODUCTS =====
        products = [
            Product(
                id=uuid4(),
                seller_id="seller-sellbot-001",
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
                id=uuid4(),
                seller_id="seller-sellbot-001",
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
                id=uuid4(),
                seller_id="seller-sellbot-001",
                sku="USB-CABLE-003",
                title="USB-C Fast Data Cable",
                description="Premium USB-C cable for fast charging",
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
                id=uuid4(),
                seller_id="seller-sellbot-001",
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
        db.flush()

        # ===== PLATFORM LISTINGS =====
        listing_specs = [
            (products[0].id, "mercado_libre", "MLA-12345678", 8.2, 425, 64),
            (products[0].id, "amazon", "B09X1Y2Z3A", 8.0, 380, 52),
            (products[0].id, "hotmart", "HM-12345678", 8.4, 250, 38),
            (products[1].id, "mercado_libre", "MLA-87654321", 7.8, 310, 45),
            (products[1].id, "amazon", "B09X2Y3Z4B", 7.6, 280, 38),
            (products[1].id, "hotmart", "HM-87654321", 8.1, 180, 28),
            (products[2].id, "mercado_libre", "MLA-11223344", 7.5, 1200, 68),
            (products[2].id, "amazon", "B09X3Y4Z5C", 7.4, 950, 55),
            (products[3].id, "hotmart", "HM-11223344", 9.2, 350, 85),
        ]

        base_prices = [99.99, 49.99, 12.99, 99.99]
        listings = []

        for prod_idx, (prod_id, platform, sku, rating, sales, count) in enumerate(listing_specs):
            listing = PlatformListing(
                id=uuid4(),
                product_id=prod_id,
                platform=platform,
                platform_sku=sku,
                listing_url=f"https://{platform}.com/{sku}",
                status="active",
                current_stock=500 if platform != "hotmart" else 350,
                current_price=base_prices[prod_idx // 3],
                rating=rating,
                rating_count=count,
                sales_this_month=sales,
                best_seller_rank=1 if sales > 300 else (3 if sales > 200 else 5),
                last_sync_at=datetime.utcnow(),
            )
            listings.append(listing)
            db.add(listing)
        db.flush()

        # ===== CUSTOMER REVIEWS =====
        review_data = [
            (5, "Excellent product, very satisfied!"),
            (5, "Amazing quality and fast shipping"),
            (4, "Good product, as described"),
            (5, "Highly recommend!"),
            (4, "Good value for money"),
        ]

        for listing in listings:
            for user_num, (rating, text) in enumerate(review_data):
                review = CustomerReview(
                    id=uuid4(),
                    listing_id=listing.id,
                    platform=listing.platform,
                    platform_review_id=f"REV-{listing.id}-{user_num}",
                    reviewer_name=f"user{user_num}",
                    rating=rating,
                    review_text=text,
                    is_flagged=False,
                    seller_response="Thank you for your feedback!",
                    response_date=datetime.utcnow(),
                    helpful_count=5 if rating == 5 else 2,
                    created_at=datetime.utcnow() - timedelta(days=10),
                )
                db.add(review)
        db.flush()

        # ===== ORDERS =====
        for listing in listings:
            for i in range(25):
                order = Order(
                    id=uuid4(),
                    platform=listing.platform,
                    platform_order_id=f"ORD-{listing.platform_sku}-{i}",
                    listing_id=listing.id,
                    product_id=listing.product_id,
                    buyer_id=f"buyer-{i}",
                    price=listing.current_price,
                    quantity=1,
                    order_status="delivered",
                    created_at=datetime.utcnow() - timedelta(days=30-i),
                    shipped_at=datetime.utcnow() - timedelta(days=28-i),
                    delivered_at=datetime.utcnow() - timedelta(days=25-i),
                )
                db.add(order)
        db.flush()

        # ===== SELLER METRICS =====
        metrics_data = [
            ("mercado_libre", 150, 8, 25, 4.8, 500, 50, 8000.0, 0.12),
            ("amazon", 120, 3, 15, 4.7, 400, 40, 6000.0, 0.10),
            ("hotmart", 80, 1, 5, 4.9, 200, 30, 4000.0, 0.15),
        ]

        for platform, active, bestseller, top5, rating, reviews, orders, gmv, conv_rate in metrics_data:
            metric = SellerMetrics(
                id=uuid4(),
                seller_id="seller-sellbot-001",
                platform=platform,
                metric_date=datetime.utcnow().date(),
                active_listings=active,
                bestseller_count=bestseller,
                top_5_count=top5,
                avg_rating=rating,
                total_reviews=reviews,
                daily_orders=orders,
                daily_gmv=gmv,
                conversion_rate=conv_rate,
                return_rate=0.02,
            )
            db.add(metric)

        db.commit()

        return {
            "status": "success",
            "products_created": len(products),
            "listings_created": len(listings),
            "reviews_created": len(listings) * len(review_data),
            "orders_created": len(listings) * 25,
            "metrics_created": 3,
            "total_gmv_monthly": 550000,
            "conversion_rate": 0.08,
            "message": "Phase 33 seed data loaded successfully!",
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
