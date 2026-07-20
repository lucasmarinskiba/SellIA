"""
Competitive Intelligence Celery Tasks

Tareas periodicas que escanean competidores y generan alertas.
"""

import asyncio
from celery import shared_task
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.competitive.intelligence_engine import CompetitiveIntelligenceEngine

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="competitive.intelligence_scanner")
def competitive_intelligence_scanner():
    """Cada 6 horas: scrapea todos los monitores activos y detecta cambios."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.domains.competitive.models import CompetitiveMonitor

            engine = CompetitiveIntelligenceEngine(db)

            result = await db.execute(
                select(CompetitiveMonitor).where(CompetitiveMonitor.status == "active")
            )
            monitors = result.scalars().all()

            scraped = 0
            changes_total = 0
            alerts_created = 0

            for monitor in monitors:
                try:
                    scrape_res = await engine.scrape_competitor(monitor.id)
                    if scrape_res.get("status") == "ok":
                        scraped += 1
                except Exception as e:
                    logger.error(f"Error scrapeando {monitor.competitor_name}: {e}")
                    continue

            # Detectar cambios por negocio
            business_ids = {m.business_id for m in monitors}
            for business_id in business_ids:
                try:
                    changes = await engine.detect_changes(business_id)
                    changes_total += len(changes)
                    for change in changes:
                        try:
                            await engine.create_alert(business_id, change)
                            alerts_created += 1
                        except Exception as e:
                            logger.error(f"Error creando alerta para {business_id}: {e}")
                except Exception as e:
                    logger.error(f"Error detectando cambios para {business_id}: {e}")

            logger.info(
                f"[Inteligencia Competitiva] monitores={len(monitors)}, "
                f"scraped={scraped}, cambios={changes_total}, alertas={alerts_created}"
            )
            return {
                "monitors": len(monitors),
                "scraped": scraped,
                "changes": changes_total,
                "alerts_created": alerts_created,
            }

    return _async_run(_run())
