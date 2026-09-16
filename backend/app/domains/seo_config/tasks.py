"""Celery tasks for SEO config operations."""

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import logging

from app.core.config import get_settings
from app.domains.seo_config.models import PublicationLink, SEOConfig
from app.domains.seo_config.platform_analytics_service import PlatformAnalyticsService
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, name="seo_config.fetch_nightly_analytics")
def fetch_nightly_analytics(self):
    """Fetch analytics for all publication links (nightly job)."""
    import asyncio

    async def _fetch():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                # Get all active publication links
                result = await db.execute(
                    select(PublicationLink).where(PublicationLink.seo_enabled == True)
                )
                links = result.scalars().all()

                analytics_svc = PlatformAnalyticsService(db)
                fetched_count = 0

                for link in links:
                    try:
                        metrics = await analytics_svc.fetch_and_store_metrics(
                            link.business_id,
                            link,
                            link.url.split("/")[-1],
                            link.connection_id,
                            date.today() - timedelta(days=1),  # Yesterday's metrics
                        )
                        if metrics:
                            fetched_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to fetch analytics for link {link.id}: {str(e)[:100]}"
                        )

                logger.info(f"Nightly analytics fetch complete: {fetched_count}/{len(links)} links")
                return {"fetched": fetched_count, "total": len(links)}

            except Exception as e:
                logger.error(f"Error in fetch_nightly_analytics: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_fetch())


@shared_task(bind=True, name="seo_config.generate_fomo_cadence")
def generate_fomo_cadence(self):
    """Generate FOMO copy for all active links without recent FOMO (cadence job)."""
    import asyncio

    async def _generate():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                # Get all active publication links
                result = await db.execute(
                    select(PublicationLink).where(PublicationLink.seo_enabled == True)
                )
                links = result.scalars().all()

                fomo_gen = PublicationFOMOGenerator(db)
                generated_count = 0

                for link in links:
                    try:
                        # Check if FOMO generation is enabled for business
                        if not await fomo_gen.is_fomo_generation_enabled(link.business_id):
                            continue

                        # Generate FOMO if not recently generated
                        fomo = await fomo_gen.generate_fomo_for_link(link.business_id, link)
                        if fomo:
                            generated_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to generate FOMO for link {link.id}: {str(e)[:100]}"
                        )

                logger.info(f"FOMO cadence complete: {generated_count}/{len(links)} links")
                return {"generated": generated_count, "total": len(links)}

            except Exception as e:
                logger.error(f"Error in generate_fomo_cadence: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_generate())


@shared_task(bind=True, name="seo_config.compute_analytics_summaries")
def compute_analytics_summaries(self):
    """Compute 7-day and 30-day performance summaries."""
    import asyncio

    async def _compute():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                # Get all publication links
                result = await db.execute(select(PublicationLink))
                links = result.scalars().all()

                analytics_svc = PlatformAnalyticsService(db)
                computed_count = 0
                today = date.today()

                for link in links:
                    try:
                        # 7-day summary
                        summary_7d = await analytics_svc.compute_performance_summary(
                            link.id,
                            today - timedelta(days=7),
                            today,
                        )
                        if summary_7d:
                            computed_count += 1

                        # 30-day summary
                        summary_30d = await analytics_svc.compute_performance_summary(
                            link.id,
                            today - timedelta(days=30),
                            today,
                        )
                        if summary_30d:
                            computed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to compute summary for link {link.id}: {str(e)[:100]}"
                        )

                logger.info(f"Analytics summaries computed: {computed_count} summaries")
                return {"computed": computed_count}

            except Exception as e:
                logger.error(f"Error in compute_analytics_summaries: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_compute())
