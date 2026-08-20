"""Competitive intelligence service — competitor tracking + market analysis."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.competitive.competitive_models import (
    Competitor, CompetitorPricing, CompetitorOffering, CompetitivePosition,
    CompetitorType, CompetitorStatus
)

logger = logging.getLogger(__name__)


class CompetitiveIntelligenceService:
    """Track competitors and analyze competitive position."""

    @staticmethod
    def add_competitor(
        business_id: UUID,
        name: str,
        competitor_type: str,
        website: str = None,
        primary_address: str = None,
        latitude: float = None,
        longitude: float = None,
        threat_level: str = "medium",
        db: Session = None
    ) -> dict:
        """Add new competitor to tracking."""
        if not db:
            raise ValueError("Database session required")

        competitor = Competitor(
            business_id=business_id,
            name=name,
            competitor_type=CompetitorType[competitor_type.upper()],
            website=website,
            primary_address=primary_address,
            latitude=latitude,
            longitude=longitude,
            threat_level=threat_level,
            status=CompetitorStatus.MONITORING
        )

        db.add(competitor)
        db.commit()
        db.refresh(competitor)

        logger.info(f"Competitor added: {name} for {business_id}")

        return {
            "competitor_id": str(competitor.id),
            "name": name,
            "type": competitor_type,
            "threat_level": threat_level
        }

    @staticmethod
    def log_competitor_pricing(
        competitor_id: UUID,
        business_id: UUID,
        product_name: str,
        base_price: Decimal,
        date: str = None,
        discounted_price: Decimal = None,
        in_stock: bool = True,
        source: str = "website",
        db: Session = None
    ) -> dict:
        """Log competitor product pricing snapshot."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        discount_pct = None
        if discounted_price and base_price > 0:
            discount_pct = Decimal(str(round(((base_price - discounted_price) / base_price) * 100, 2)))

        pricing = CompetitorPricing(
            competitor_id=competitor_id,
            business_id=business_id,
            product_name=product_name,
            base_price=base_price,
            discount_active=discounted_price is not None,
            discounted_price=discounted_price,
            discount_pct=discount_pct,
            in_stock=in_stock,
            date_observed=date,
            source=source
        )

        db.add(pricing)
        db.commit()

        logger.info(f"Pricing logged: {product_name} - {base_price}")

        return {
            "product": product_name,
            "base_price": float(base_price),
            "discounted_price": float(discounted_price) if discounted_price else None,
            "discount_pct": float(discount_pct) if discount_pct else None,
            "date": date
        }

    @staticmethod
    def add_competitor_offering(
        competitor_id: UUID,
        business_id: UUID,
        offering_type: str,
        offering_name: str,
        category: str = None,
        description: str = None,
        features: List[str] = None,
        our_has_equivalent: bool = False,
        competitive_advantage: str = None,
        db: Session = None
    ) -> dict:
        """Log competitor product/service offering."""
        if not db:
            raise ValueError("Database session required")

        offering = CompetitorOffering(
            competitor_id=competitor_id,
            business_id=business_id,
            offering_type=offering_type,
            offering_name=offering_name,
            category=category,
            description=description,
            features=features or [],
            our_has_equivalent=our_has_equivalent,
            competitive_advantage=competitive_advantage
        )

        db.add(offering)
        db.commit()
        db.refresh(offering)

        logger.info(f"Offering logged: {offering_name} from competitor {competitor_id}")

        return {
            "offering_id": str(offering.id),
            "offering_name": offering_name,
            "category": category,
            "our_has_equivalent": our_has_equivalent
        }

    @staticmethod
    def get_competitive_position(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Get competitive position summary."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Count competitors
        all_competitors = db.query(Competitor).filter(
            Competitor.business_id == business_id,
            Competitor.status == CompetitorStatus.ACTIVE
        ).all()

        total_competitors = len(all_competitors)
        direct_competitors = len([c for c in all_competitors if c.competitor_type == CompetitorType.DIRECT])
        high_threat = len([c for c in all_competitors if c.threat_level == "critical" or c.threat_level == "high"])

        # Price analysis
        pricing_data = db.query(CompetitorPricing).filter(
            CompetitorPricing.business_id == business_id,
            CompetitorPricing.date_observed == date
        ).all()

        avg_competitor_price = None
        if pricing_data:
            prices = [float(p.base_price) for p in pricing_data if p.base_price]
            avg_competitor_price = Decimal(str(sum(prices) / len(prices))) if prices else None

        # Rating analysis
        ratings = [float(c.google_rating) for c in all_competitors if c.google_rating]
        avg_rating = Decimal(str(sum(ratings) / len(ratings))) if ratings else None
        avg_reviews = sum(c.google_review_count for c in all_competitors) // max(len(all_competitors), 1)

        # Discount frequency
        discounts = [p.discount_pct for p in pricing_data if p.discount_pct]
        most_common_discount = Decimal(str(sum(discounts) / len(discounts))) if discounts else None

        position = CompetitivePosition(
            business_id=business_id,
            date=date,
            total_competitors_tracked=total_competitors,
            direct_competitors=direct_competitors,
            high_threat_count=high_threat,
            avg_competitor_price=avg_competitor_price,
            avg_competitor_rating=avg_rating,
            avg_review_count=avg_reviews,
            most_common_discount_pct=most_common_discount
        )

        db.add(position)
        db.commit()

        logger.info(f"Competitive position calculated: {business_id} - {date}")

        return {
            "position_calculated": True,
            "date": date,
            "competitor_counts": {
                "total": total_competitors,
                "direct": direct_competitors,
                "high_threat": high_threat
            },
            "market_metrics": {
                "avg_competitor_price": float(avg_competitor_price) if avg_competitor_price else None,
                "avg_competitor_rating": float(avg_rating) if avg_rating else None,
                "avg_review_count": avg_reviews,
                "most_common_discount_pct": float(most_common_discount) if most_common_discount else None
            }
        }

    @staticmethod
    def get_price_benchmarking(
        business_id: UUID,
        product_name: str,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Compare our pricing vs competitors."""
        if not db:
            raise ValueError("Database session required")

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        # Get competitor pricing for product
        competitor_pricing = db.query(CompetitorPricing).filter(
            CompetitorPricing.business_id == business_id,
            CompetitorPricing.product_name.ilike(f"%{product_name}%"),
            CompetitorPricing.date_observed >= cutoff
        ).all()

        if not competitor_pricing:
            return {"benchmarking_available": False}

        # Latest price per competitor
        by_competitor: Dict[str, dict] = {}
        for pricing in competitor_pricing:
            comp_id = str(pricing.competitor_id)
            if comp_id not in by_competitor or pricing.date_observed > by_competitor[comp_id]["date"]:
                by_competitor[comp_id] = {
                    "date": pricing.date_observed,
                    "price": float(pricing.base_price),
                    "discounted": float(pricing.discounted_price) if pricing.discounted_price else None
                }

        prices = [p["price"] for p in by_competitor.values()]
        if not prices:
            return {"benchmarking_available": False}

        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        return {
            "benchmarking_available": True,
            "product": product_name,
            "days": days,
            "competitor_count": len(by_competitor),
            "price_range": {
                "min": min_price,
                "max": max_price,
                "avg": round(avg_price, 2)
            },
            "competitors": [
                {
                    "competitor_id": cid,
                    "price": data["price"],
                    "discounted": data["discounted"]
                }
                for cid, data in list(by_competitor.items())[:10]
            ]
        }

    @staticmethod
    def get_offering_gaps(
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Identify feature/offering gaps vs competitors."""
        if not db:
            raise ValueError("Database session required")

        offerings = db.query(CompetitorOffering).filter(
            CompetitorOffering.business_id == business_id
        ).all()

        if not offerings:
            return {"gaps_identified": 0}

        # Group by category
        by_category: Dict[str, list] = {}
        for offering in offerings:
            cat = offering.category or "other"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(offering)

        gaps = []
        for category, items in by_category.items():
            missing = [o for o in items if not o.our_has_equivalent]
            if missing:
                gaps.append({
                    "category": category,
                    "gaps": len(missing),
                    "offerings": [
                        {
                            "offering": o.offering_name,
                            "competitor": str(o.competitor_id),
                            "advantage": o.competitive_advantage
                        }
                        for o in missing[:5]
                    ]
                })

        return {
            "total_gaps": len(gaps),
            "by_category": gaps
        }

    @staticmethod
    def get_competitor_list(
        business_id: UUID,
        threat_level: Optional[str] = None,
        limit: int = 20,
        db: Session = None
    ) -> dict:
        """Get list of tracked competitors."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(Competitor).filter(Competitor.business_id == business_id)

        if threat_level:
            query = query.filter(Competitor.threat_level == threat_level)

        competitors = query.order_by(Competitor.updated_at.desc()).limit(limit).all()

        return {
            "competitor_count": len(competitors),
            "competitors": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "type": c.competitor_type.value,
                    "threat_level": c.threat_level,
                    "website": c.website,
                    "google_rating": float(c.google_rating) if c.google_rating else None,
                    "followers": c.social_media_followers,
                    "location": c.primary_address
                }
                for c in competitors
            ]
        }
