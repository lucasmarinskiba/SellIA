"""Marketing attribution service — calculate channel ROI + multi-touch attribution."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, List
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.attribution.attribution_models import (
    ChannelAttributionMetric, LocationChannelAttribution, ChannelROIReport,
    AttributionModel
)
from app.domains.journeys.journey_models import (
    CustomerJourney, JourneyTouchpoint, JourneyChannel
)

logger = logging.getLogger(__name__)


class ChannelAttributionService:
    """Calculate channel ROI and multi-touch attribution."""

    @staticmethod
    def calculate_channel_metrics(
        business_id: UUID,
        channel: str,
        date: str,
        db: Session = None
    ) -> dict:
        """Calculate attribution metrics for channel on given date."""
        if not db:
            raise ValueError("Database session required")

        date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        # Get journeys initiated via channel
        journeys = db.query(CustomerJourney).filter(
            CustomerJourney.business_id == business_id,
            CustomerJourney.initial_channel == JourneyChannel[channel.upper()],
            CustomerJourney.awareness_date >= date_start,
            CustomerJourney.awareness_date < date_end
        ).all()

        if not journeys:
            return {"metrics_calculated": False, "channel": channel, "date": date}

        journeys_initiated = len(journeys)
        journeys_with_visit = len([j for j in journeys if j.visit_date])
        visit_rate = (journeys_with_visit / max(journeys_initiated, 1)) * 100

        # Revenue from journeys
        revenue = Decimal("0")
        orders = 0
        for j in journeys:
            if j.first_order_value:
                revenue += j.first_order_value
                orders += 1
            if j.total_lifetime_value:
                revenue = max(revenue, j.total_lifetime_value)

        aov = revenue / max(orders, 1) if orders > 0 else Decimal("0")

        # Check or create metric
        existing = db.query(ChannelAttributionMetric).filter(
            ChannelAttributionMetric.business_id == business_id,
            ChannelAttributionMetric.channel == channel,
            ChannelAttributionMetric.date == date
        ).first()

        if existing:
            existing.journeys_initiated = journeys_initiated
            existing.journeys_with_visit = journeys_with_visit
            existing.visit_rate = Decimal(str(round(visit_rate, 2)))
            existing.revenue_attributed = revenue
            existing.orders_attributed = orders
            existing.aov = aov
        else:
            existing = ChannelAttributionMetric(
                business_id=business_id,
                channel=channel,
                date=date,
                journeys_initiated=journeys_initiated,
                journeys_with_visit=journeys_with_visit,
                visit_rate=Decimal(str(round(visit_rate, 2))),
                revenue_attributed=revenue,
                orders_attributed=orders,
                aov=aov
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        logger.info(f"Channel metrics calculated: {business_id} - {channel} - {date}")

        return {
            "channel": channel,
            "date": date,
            "journeys_initiated": journeys_initiated,
            "journeys_with_visit": journeys_with_visit,
            "visit_rate_pct": float(visit_rate),
            "revenue": float(revenue),
            "orders": orders,
            "aov": float(aov) if aov else 0
        }

    @staticmethod
    def attribute_visits_to_channel(
        business_id: UUID,
        location_id: UUID,
        attribution_model: AttributionModel = AttributionModel.FIRST_TOUCH,
        date_start: str = None,
        date_end: str = None,
        db: Session = None
    ) -> dict:
        """Attribute location visits to channels."""
        if not db:
            raise ValueError("Database session required")

        if not date_start:
            date_start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_end:
            date_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        date_start_dt = datetime.fromisoformat(f"{date_start}T00:00:00+00:00")
        date_end_dt = datetime.fromisoformat(f"{date_end}T23:59:59+00:00")

        # Get journeys with visits at location in period
        journeys = db.query(CustomerJourney).filter(
            CustomerJourney.business_id == business_id,
            CustomerJourney.location_visited_id == location_id,
            CustomerJourney.visit_date >= date_start_dt,
            CustomerJourney.visit_date <= date_end_dt
        ).all()

        if not journeys:
            return {"attribution_calculated": False, "location_id": str(location_id)}

        # Group by channel
        by_channel: Dict[str, list] = {}
        for j in journeys:
            ch = j.initial_channel.value
            if ch not in by_channel:
                by_channel[ch] = []
            by_channel[ch].append(j)

        # Create attribution record per channel
        results = []
        for channel, channel_journeys in by_channel.items():
            visits = len(channel_journeys)
            orders = len([j for j in channel_journeys if j.is_converted])
            conversion_rate = (orders / max(visits, 1)) * 100

            revenue = Decimal("0")
            for j in channel_journeys:
                if j.first_order_value:
                    revenue += j.first_order_value

            rpv = revenue / max(visits, 1) if visits > 0 else Decimal("0")

            record = LocationChannelAttribution(
                business_id=business_id,
                location_id=location_id,
                channel=channel,
                attribution_model=attribution_model,
                date_start=date_start,
                date_end=date_end,
                visits_attributed=visits,
                revenue_attributed=revenue,
                orders_from_visits=orders,
                conversion_rate=Decimal(str(round(conversion_rate, 2))),
                revenue_per_visit=rpv
            )
            db.add(record)
            results.append({
                "channel": channel,
                "visits": visits,
                "orders": orders,
                "conversion_rate_pct": float(conversion_rate),
                "revenue": float(revenue),
                "revenue_per_visit": float(rpv)
            })

        db.commit()
        logger.info(f"Attribution calculated: {location_id} - {len(results)} channels")

        return {
            "attribution_calculated": True,
            "location_id": str(location_id),
            "period": f"{date_start} to {date_end}",
            "by_channel": results
        }

    @staticmethod
    def generate_channel_roi_report(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Generate ROI ranking by channel."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metrics = db.query(ChannelAttributionMetric).filter(
            ChannelAttributionMetric.business_id == business_id,
            ChannelAttributionMetric.date == date
        ).all()

        if not metrics:
            return {"roi_report_generated": False, "date": date}

        # Rankings
        by_visits = sorted(metrics, key=lambda m: m.journeys_with_visit, reverse=True)
        by_revenue = sorted(metrics, key=lambda m: m.revenue_attributed, reverse=True)
        by_roas = sorted(metrics, key=lambda m: m.roas, reverse=True) if any(m.roas for m in metrics) else []

        total_cost = sum(float(m.cost) for m in metrics)
        total_revenue = sum(float(m.revenue_attributed) for m in metrics)
        total_visits = sum(m.journeys_with_visit for m in metrics)
        blended_roas = (total_revenue / max(total_cost, 1)) if total_cost > 0 else Decimal("0")
        blended_cpv = (Decimal(str(total_cost)) / max(total_visits, 1)) if total_visits > 0 else Decimal("0")

        report = ChannelROIReport(
            business_id=business_id,
            date=date,
            channel_rank_by_visits=by_visits[0].channel if by_visits else None,
            channel_rank_by_revenue=by_revenue[0].channel if by_revenue else None,
            channel_rank_by_roas=by_roas[0].channel if by_roas else None,
            total_cost=Decimal(str(total_cost)),
            total_revenue=Decimal(str(total_revenue)),
            total_visits=total_visits,
            blended_roas=blended_roas,
            blended_cpv=blended_cpv
        )

        db.add(report)
        db.commit()

        logger.info(f"ROI report generated: {business_id} - {date}")

        return {
            "roi_report_generated": True,
            "date": date,
            "rankings": {
                "best_visits": by_visits[0].channel if by_visits else None,
                "best_revenue": by_revenue[0].channel if by_revenue else None,
                "best_roas": by_roas[0].channel if by_roas else None
            },
            "totals": {
                "cost": float(total_cost),
                "revenue": float(total_revenue),
                "visits": total_visits,
                "blended_roas": float(blended_roas),
                "blended_cpv": float(blended_cpv)
            },
            "channels": [
                {
                    "channel": m.channel,
                    "visits": m.journeys_with_visit,
                    "revenue": float(m.revenue_attributed),
                    "roas": float(m.roas) if m.roas else None
                }
                for m in metrics
            ]
        }

    @staticmethod
    def get_top_performing_channels(
        business_id: UUID,
        metric: str = "revenue",
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get top N channels by metric (revenue, visits, roas)."""
        if not db:
            raise ValueError("Database session required")

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        metrics = db.query(ChannelAttributionMetric).filter(
            ChannelAttributionMetric.business_id == business_id,
            ChannelAttributionMetric.date >= cutoff
        ).all()

        if not metrics:
            return {"channels": []}

        # Aggregate by channel
        by_channel: Dict[str, dict] = {}
        for m in metrics:
            if m.channel not in by_channel:
                by_channel[m.channel] = {
                    "cost": Decimal("0"),
                    "revenue": Decimal("0"),
                    "visits": 0,
                    "orders": 0
                }
            by_channel[m.channel]["cost"] += m.cost
            by_channel[m.channel]["revenue"] += m.revenue_attributed
            by_channel[m.channel]["visits"] += m.journeys_with_visit
            by_channel[m.channel]["orders"] += m.orders_attributed

        # Sort by metric
        if metric == "revenue":
            sorted_channels = sorted(by_channel.items(), key=lambda x: x[1]["revenue"], reverse=True)
        elif metric == "visits":
            sorted_channels = sorted(by_channel.items(), key=lambda x: x[1]["visits"], reverse=True)
        else:  # roas
            sorted_channels = sorted(
                by_channel.items(),
                key=lambda x: (x[1]["revenue"] / max(x[1]["cost"], 1)),
                reverse=True
            )

        return {
            "metric": metric,
            "days": days,
            "channels": [
                {
                    "channel": ch,
                    "cost": float(data["cost"]),
                    "revenue": float(data["revenue"]),
                    "visits": data["visits"],
                    "orders": data["orders"],
                    "roas": float(data["revenue"] / max(data["cost"], 1)) if data["cost"] > 0 else None,
                    "cpv": float(data["cost"] / max(data["visits"], 1)) if data["visits"] > 0 else None
                }
                for ch, data in sorted_channels[:10]
            ]
        }
