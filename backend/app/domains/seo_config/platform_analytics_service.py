"""Service to fetch and store analytics from platforms."""

from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink
from app.domains.seo_config.analytics_models import PublicationLinkMetrics, PublicationLinkPerformanceSummary
from app.domains.seo_config.platform_analytics_mercadolibre import MercadoLibreAnalytics
from app.domains.seo_config.platform_analytics_base import PlatformAnalyticsConnector

logger = get_logger(__name__)

ANALYTICS_CONNECTORS = {
    "mercado-libre": MercadoLibreAnalytics,
    # "shopify": ShopifyAnalytics,
    # "instagram": InstagramAnalytics,
}


class PlatformAnalyticsService:
    """Fetch and store performance metrics from platforms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_analytics_connector(
        self, platform_name: str, connection_id: UUID
    ) -> PlatformAnalyticsConnector | None:
        """Get analytics connector for platform."""
        if platform_name not in ANALYTICS_CONNECTORS:
            logger.warning(f"No analytics connector for platform: {platform_name}")
            return None

        try:
            from app.domains.integrations.integration_models import IntegrationConnection

            result = await self.db.execute(
                select(IntegrationConnection).where(
                    IntegrationConnection.id == connection_id
                )
            )
            connection = result.scalar_one_or_none()

            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return None

            credentials = connection.auth_metadata or {}
            if connection.auth_token:
                credentials["access_token"] = connection.auth_token

            connector_class = ANALYTICS_CONNECTORS[platform_name]
            connector = connector_class(credentials)

            if not await connector.validate_credentials():
                logger.error(f"Analytics credentials invalid for {platform_name}")
                return None

            return connector

        except Exception as e:
            logger.error(f"Error getting analytics connector: {str(e)[:200]}")
            return None

    async def fetch_and_store_metrics(
        self,
        business_id: UUID,
        link: PublicationLink,
        external_id: str,
        connection_id: UUID | None = None,
        metric_date: date | None = None,
    ) -> PublicationLinkMetrics | None:
        """Fetch metrics for one link and store in DB."""
        metric_date = metric_date or date.today()

        # Check if metrics already fetched for today
        existing = await self.db.execute(
            select(PublicationLinkMetrics).where(
                PublicationLinkMetrics.link_id == link.id,
                PublicationLinkMetrics.metric_date == metric_date,
            )
        )
        if existing.scalar_one_or_none():
            logger.info(f"Metrics already fetched for {link.id} on {metric_date}")
            return None

        try:
            connector = await self.get_analytics_connector(link.platform_source, connection_id)
            if not connector:
                logger.warning(f"No connector for {link.platform_source}")
                return None

            # Fetch metrics from platform
            metrics_data = await connector.get_listing_metrics(
                external_id,
                metric_date - timedelta(days=1),
                metric_date,
            )

            # Parse metrics
            impressions = metrics_data.get("impressions", 0)
            clicks = metrics_data.get("clicks", 0)
            conversions = metrics_data.get("conversions", 0)
            revenue = metrics_data.get("revenue", 0)
            clicks_estimated = metrics_data.get("clicks_estimated", False)
            conversions_estimated = metrics_data.get("conversions_estimated", False)
            revenue_estimated = metrics_data.get("revenue_estimated", False)

            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            conv_rate = (conversions / clicks * 100) if clicks > 0 else 0

            # Store metrics
            metrics = PublicationLinkMetrics(
                business_id=business_id,
                link_id=link.id,
                metric_date=metric_date,
                platform_name=link.platform_source,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                ctr=ctr,
                conversion_rate=conv_rate,
                revenue=revenue,
                clicks_estimated=clicks_estimated,
                conversions_estimated=conversions_estimated,
                revenue_estimated=revenue_estimated,
                data_source="api",
            )

            self.db.add(metrics)
            await self.db.commit()
            await self.db.refresh(metrics)

            logger.info(
                f"Stored metrics for {link.id}: impressions={impressions}, "
                f"clicks={clicks}, conversions={conversions}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error fetching metrics for {link.id}: {str(e)[:200]}")
            return None

    async def compute_performance_summary(
        self,
        link_id: UUID,
        period_start: date,
        period_end: date,
    ) -> PublicationLinkPerformanceSummary | None:
        """Compute aggregated performance summary for a period."""
        try:
            # Get all metrics for the period
            result = await self.db.execute(
                select(PublicationLinkMetrics).where(
                    PublicationLinkMetrics.link_id == link_id,
                    PublicationLinkMetrics.metric_date >= period_start,
                    PublicationLinkMetrics.metric_date <= period_end,
                )
            )
            metrics_list = result.scalars().all()

            if not metrics_list:
                logger.warning(f"No metrics found for {link_id} in period")
                return None

            # Aggregate
            total_impressions = sum(m.impressions for m in metrics_list)
            total_clicks = sum(m.clicks for m in metrics_list)
            total_conversions = sum(m.conversions for m in metrics_list)
            total_revenue = sum(m.revenue for m in metrics_list)

            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            avg_conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

            business_id = metrics_list[0].business_id

            summary = PublicationLinkPerformanceSummary(
                business_id=business_id,
                link_id=link_id,
                period_start=period_start,
                period_end=period_end,
                total_impressions=total_impressions,
                total_clicks=total_clicks,
                total_conversions=total_conversions,
                total_revenue=total_revenue,
                avg_ctr=avg_ctr,
                avg_conversion_rate=avg_conv_rate,
            )

            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)

            logger.info(f"Computed summary for {link_id}: {total_conversions} conversions")
            return summary

        except Exception as e:
            logger.error(f"Error computing summary: {str(e)[:200]}")
            return None
