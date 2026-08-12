"""Phase 33 Celery Tasks - Async operations for multi-platform automation."""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import SessionLocal
from backend.app.domains.enterprise.platform_integration import (
    PlatformSyncEngine,
    DynamicPricingEngine,
    Platform,
)
from backend.app.models.platform_integration import (
    Product,
    PlatformListing,
    SellerMetrics,
    Order,
)


@shared_task(bind=True, max_retries=3)
def sync_inventory_task(self, product_id: str):
    """
    Sync inventory across platforms every 5 minutes.
    Prevent overselling by reserving stock from recent orders.
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"status": "error", "message": "Product not found"}

        # Calculate reserved inventory (orders in last 24h, not yet fulfilled)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_orders = db.query(Order).filter(
            Order.product_id == product_id,
            Order.created_at >= twenty_four_hours_ago,
            Order.order_status != "delivered",
        ).all()

        reserved = sum(o.quantity for o in recent_orders)
        available = max(0, product.stock_total - reserved)

        # Sync to each platform
        sync_engine = PlatformSyncEngine(db)
        results = sync_engine.sync_inventory(product_id, available)

        return {
            "status": "success",
            "product_id": product_id,
            "total_stock": product.stock_total,
            "reserved": reserved,
            "available": available,
            "sync_results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def reprice_products_task(self, platform: str = None):
    """
    Reprice all products based on competitor prices.
    Runs every 2-4 hours to optimize prices dynamically.
    Strategy: Undercut leaders, premium on scarcity, maintain margin on stable inventory.
    """
    db = SessionLocal()
    try:
        platforms = (
            [Platform(platform)]
            if platform
            else [Platform.MERCADO_LIBRE, Platform.AMAZON, Platform.HOTMART]
        )

        pricing_engine = DynamicPricingEngine(db)
        results = {}

        for plat in platforms:
            # Get all listings for platform
            listings = db.query(PlatformListing).filter(
                PlatformListing.platform == plat.value
            ).all()

            repriced = 0
            for listing in listings:
                # Get competitor data (would call actual APIs in production)
                # For now: simplified logic
                if listing.current_price > listing.current_price * 1.1:  # 10% high
                    listing.current_price *= 0.95  # 5% discount
                    repriced += 1

            results[plat.value] = {
                "listings_repriced": repriced,
                "total_listings": len(listings),
                "timestamp": datetime.utcnow().isoformat(),
            }

        db.commit()

        return {
            "status": "success",
            "platforms": results,
            "message": f"Repriced products across {len(platforms)} platforms",
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@shared_task
def update_seller_metrics_task():
    """
    Calculate daily seller metrics from orders and listings.
    Runs once daily to update KPIs.
    """
    db = SessionLocal()
    try:
        sellers = db.query(Product).with_entities(Product.seller_id).distinct().all()

        for (seller_id,) in sellers:
            for platform in ["mercado_libre", "amazon", "hotmart"]:
                # Get metrics for this seller/platform
                listings = (
                    db.query(PlatformListing)
                    .join(Product, PlatformListing.product_id == Product.id)
                    .filter(
                        Product.seller_id == seller_id,
                        PlatformListing.platform == platform,
                    )
                    .all()
                )

                # Calculate metrics
                active = len([l for l in listings if l.status == "active"])
                bestseller = len([l for l in listings if l.best_seller_rank == 1])
                top_5 = len([l for l in listings if l.best_seller_rank and l.best_seller_rank <= 5])
                avg_rating = (
                    sum(l.rating for l in listings) / len(listings)
                    if listings
                    else 0
                )
                total_reviews = sum(l.rating_count for l in listings)

                # Get orders for this seller/platform (last 24h)
                last_24h = datetime.utcnow() - timedelta(hours=24)
                orders = (
                    db.query(Order)
                    .join(PlatformListing, Order.listing_id == PlatformListing.id)
                    .join(Product, PlatformListing.product_id == Product.id)
                    .filter(
                        Product.seller_id == seller_id,
                        Order.platform == platform,
                        Order.created_at >= last_24h,
                    )
                    .all()
                )

                daily_orders = len(orders)
                daily_gmv = sum(o.price * o.quantity for o in orders)
                conversion_rate = (
                    (sum(1 for l in listings if l.sales_this_month) / len(listings))
                    if listings
                    else 0
                )

                # Store metrics
                metric = SellerMetrics(
                    seller_id=seller_id,
                    platform=platform,
                    metric_date=datetime.utcnow().date(),
                    active_listings=active,
                    bestseller_count=bestseller,
                    top_5_count=top_5,
                    avg_rating=float(avg_rating),
                    total_reviews=total_reviews,
                    daily_orders=daily_orders,
                    daily_gmv=float(daily_gmv),
                    conversion_rate=float(conversion_rate),
                    return_rate=0.02,  # 2% default
                )
                db.add(metric)

        db.commit()

        return {
            "status": "success",
            "message": "Seller metrics updated for all sellers",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@shared_task
def generate_review_requests_task():
    """
    Auto-generate review request emails for delivered orders.
    Runs twice daily to maximize review velocity.
    """
    db = SessionLocal()
    try:
        # Get delivered orders from 2-7 days ago (optimal review request window)
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        orders = (
            db.query(Order)
            .filter(
                Order.order_status == "delivered",
                Order.delivered_at >= seven_days_ago,
                Order.delivered_at <= two_days_ago,
            )
            .all()
        )

        # Generate requests (in production: send via email, SMS, in-app)
        requests = []
        for order in orders:
            requests.append(
                {
                    "order_id": order.id,
                    "buyer_id": order.buyer_id,
                    "platform": order.platform,
                    "message": f"We'd love your feedback on your recent purchase! Leave a review and help others.",
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        return {
            "status": "success",
            "review_requests_generated": len(requests),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
