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


@shared_task(bind=True, name="seo_config.check_ab_test_winners")
def check_ab_test_winners(self):
    """Check running A/B tests and announce winners when threshold reached."""
    import asyncio

    async def _check():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                from app.domains.seo_config.fomo_abtest_service import FOMABTestService
                from app.domains.seo_config.fomo_models import FOMABTest

                # Get all running tests
                result = await db.execute(
                    select(FOMABTest).where(FOMABTest.status == "running")
                )
                running_tests = result.scalars().all()

                ab_svc = FOMABTestService(db)
                winners_announced = 0

                for test in running_tests:
                    try:
                        updated_test = await ab_svc.check_and_announce_winner(test.id)
                        if updated_test and updated_test.status == "completed":
                            winners_announced += 1
                    except Exception as e:
                        logger.error(f"Failed to check test {test.id}: {str(e)[:100]}")

                logger.info(f"A/B test check complete: {winners_announced} winners announced")
                return {"winners_announced": winners_announced}

            except Exception as e:
                logger.error(f"Error in check_ab_test_winners: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_check())


@shared_task(bind=True, name="seo_config.monitor_fomo_decay")
def monitor_fomo_decay(self):
    """Monitor FOMO copy decay and auto-rotate when detected."""
    import asyncio

    async def _monitor():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                from app.domains.seo_config.fomo_decay_service import FOMADecayService
                from app.domains.seo_config.fomo_auto_rotation import FOMAAutoRotator
                from app.domains.businesses.models import Business

                # Get all active businesses
                result = await db.execute(select(Business).where(Business.active == True))
                businesses = result.scalars().all()

                decay_svc = FOMADecayService(db)
                rotator = FOMAAutoRotator(db)
                total_decay_detected = 0
                total_rotated = 0

                for business in businesses:
                    try:
                        # Detect decay for all links
                        decayed = await decay_svc.get_links_with_decay(
                            business.id,
                            decay_threshold_pct=30.0,
                        )

                        for item in decayed:
                            # Log decay
                            await decay_svc.log_decay_and_regenerate(
                                business.id,
                                item["link"]["id"],
                                item["baseline_ctr"],
                                item["current_ctr"],
                                item["decay_percentage"],
                                action="regenerate",
                            )
                            total_decay_detected += 1

                        # Auto-rotate decayed links
                        rotation_result = await rotator.auto_rotate_on_decay(business.id)
                        total_rotated += rotation_result.get('rotated', 0)

                    except Exception as e:
                        logger.error(f"Failed to monitor decay for business {business.id}: {str(e)[:100]}")

                logger.info(f"FOMO decay monitor complete: {total_decay_detected} decays detected, {total_rotated} auto-rotated")
                return {
                    "decay_detected": total_decay_detected,
                    "auto_rotated": total_rotated,
                }

            except Exception as e:
                logger.error(f"Error in monitor_fomo_decay: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_monitor())


@shared_task(bind=True, name="seo_config.compute_positioning_scores")
def compute_positioning_scores(self):
    """Nightly: compute platform-algorithm-aware positioning score for every
    active publication link that has a ranking connector available."""
    import asyncio

    async def _compute():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                from app.domains.seo_config.positioning_score_service import PositioningScoreService

                result = await db.execute(
                    select(PublicationLink).where(PublicationLink.seo_enabled == True)
                )
                # Snapshot ids only: after a rollback every loaded ORM instance is expired,
                # so each link is re-fetched inside the loop instead of reused.
                link_ids = [link.id for link in result.scalars().all()]

                service = PositioningScoreService(db)
                computed = 0

                for link_id in link_ids:
                    try:
                        link = await db.get(PublicationLink, link_id)
                        if not link:
                            continue
                        score = await service.compute_score_for_link(
                            link.business_id, link, link.connection_id
                        )
                        if score:
                            computed += 1
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Failed to compute positioning for link {link_id}: {str(e)[:100]}")

                logger.info(f"Positioning score compute complete: {computed}/{len(link_ids)} links")
                return {"computed": computed, "total": len(link_ids)}

            except Exception as e:
                logger.error(f"Error in compute_positioning_scores: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_compute())

    return asyncio.run(_monitor())


@shared_task(bind=True, name="seo_config.compute_store_positioning_scores")
def compute_store_positioning_scores(self):
    """Nightly: store-level positioning for every active Amazon Brand Store connection.

    A connection counts as a Brand Store (Ads API) connection when its
    auth_metadata carries `brand_entity_id` — the credential contract of
    AmazonStoreRankingConnector. IntegrationApp has no seeded platform slug to
    filter on, and an SP-API-only connection must not be sent to the Ads API.
    """
    import asyncio

    async def _compute():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                from app.domains.integrations.integration_models import IntegrationConnection
                from app.domains.seo_config.store_positioning_service import StorePositioningScoreService

                result = await db.execute(
                    select(IntegrationConnection).where(
                        IntegrationConnection.connection_status == "active",
                        IntegrationConnection.auth_metadata.has_key("brand_entity_id"),
                    )
                )
                connections = result.scalars().all()
                # Snapshot plain values first: a rollback inside the loop expires ORM instances.
                targets = [(c.business_id, c.id) for c in connections]

                service = StorePositioningScoreService(db)
                computed = 0

                for business_id, connection_id in targets:
                    try:
                        score = await service.compute_store_score(business_id, "amazon", connection_id)
                        if score:
                            computed += 1
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Failed to compute store positioning for business {business_id}: {str(e)[:100]}")

                logger.info(f"Store positioning compute complete: {computed}/{len(targets)} connections")
                return {"computed": computed, "total": len(targets)}

            except Exception as e:
                logger.error(f"Error in compute_store_positioning_scores: {str(e)[:200]}")
                raise
            finally:
                await engine.dispose()

    return asyncio.run(_compute())
