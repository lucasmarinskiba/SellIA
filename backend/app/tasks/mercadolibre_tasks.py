"""Tareas de Mercado Libre: sincronización periódica de órdenes."""

from celery import shared_task

from app.core.async_bridge import run_async


@shared_task
def sync_mercadolibre_orders_task() -> dict:
    """Trae órdenes nuevas o cambiadas de los canales de Mercado Libre. Corre cada 15 minutos."""

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.domains.orders.marketplace_orders import reconcile_mercadolibre_orders

        async with AsyncSessionLocal() as db:
            return await reconcile_mercadolibre_orders(db)

    return run_async(_run())
