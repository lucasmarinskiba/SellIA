"""
Orders Scheduler — Ejecuta sync automático cada 5 minutos (24/7).

Background job: Mercado Libre, Amazon, Shopify orders sync
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class OrdersScheduler:
    """Scheduler para sincronizar órdenes automáticamente."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False

    def start(self):
        """Inicia scheduler."""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("Orders scheduler started")

    def stop(self):
        """Para scheduler."""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Orders scheduler stopped")

    async def add_mercadolibre_sync(
        self,
        seller_id: str,
        access_token: str,
        ml_service,  # MercadoLibreAutomation instance
        interval_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Agenda sync de órdenes Mercado Libre.

        Ejecuta automáticamente cada N minutos.
        """

        logger.info(f"Adding ML sync job for seller {seller_id} (every {interval_minutes}min)")

        job_id = f"ml_sync_{seller_id}"

        try:
            self.scheduler.add_job(
                self._sync_ml_orders_wrapper,
                IntervalTrigger(minutes=interval_minutes),
                args=[ml_service, seller_id],
                id=job_id,
                name=f"ML Sync - {seller_id}",
                replace_existing=True,
            )

            logger.info(f"Job added: {job_id}")

            return {
                "status": "success",
                "job_id": job_id,
                "interval_minutes": interval_minutes,
                "next_run": self.scheduler.get_job(job_id).next_run_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Add ML sync job failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def add_amazon_sync(
        self,
        seller_id: str,
        mws_token: str,
        amazon_service,
        interval_minutes: int = 10,
    ) -> Dict[str, Any]:
        """Agenda sync de órdenes Amazon."""

        logger.info(f"Adding Amazon sync job for {seller_id}")

        job_id = f"amazon_sync_{seller_id}"

        try:
            self.scheduler.add_job(
                self._sync_amazon_orders_wrapper,
                IntervalTrigger(minutes=interval_minutes),
                args=[amazon_service, seller_id],
                id=job_id,
                name=f"Amazon Sync - {seller_id}",
                replace_existing=True,
            )

            return {
                "status": "success",
                "job_id": job_id,
                "interval_minutes": interval_minutes,
            }

        except Exception as e:
            logger.error(f"Add Amazon sync job failed: {str(e)}")
            return {"status": "error"}

    async def add_shopify_sync(
        self,
        store_url: str,
        access_token: str,
        shopify_service,
        interval_minutes: int = 10,
    ) -> Dict[str, Any]:
        """Agenda sync de órdenes Shopify."""

        logger.info(f"Adding Shopify sync job for {store_url}")

        job_id = f"shopify_sync_{store_url}"

        try:
            self.scheduler.add_job(
                self._sync_shopify_orders_wrapper,
                IntervalTrigger(minutes=interval_minutes),
                args=[shopify_service, store_url],
                id=job_id,
                name=f"Shopify Sync - {store_url}",
                replace_existing=True,
            )

            return {
                "status": "success",
                "job_id": job_id,
                "interval_minutes": interval_minutes,
            }

        except Exception as e:
            logger.error(f"Add Shopify sync job failed: {str(e)}")
            return {"status": "error"}

    def remove_job(self, job_id: str) -> Dict[str, Any]:
        """Elimina job."""

        logger.info(f"Removing job {job_id}")

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Remove job failed: {str(e)}")
            return {"status": "error"}

    def list_jobs(self) -> Dict[str, Any]:
        """Lista todos los jobs activos."""

        jobs = self.scheduler.get_jobs()

        return {
            "status": "success",
            "jobs_count": len(jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
                for job in jobs
            ],
        }

    # ========== WRAPPERS (para ejecutar en background) ==========

    @staticmethod
    async def _sync_ml_orders_wrapper(ml_service, seller_id: str):
        """Wrapper para ejecutar ML sync en background."""
        try:
            logger.info(f"Executing ML sync for {seller_id}")
            result = await ml_service.sync_orders()
            logger.info(f"ML sync complete: {result.get('orders_synced', 0)} orders")
        except Exception as e:
            logger.error(f"ML sync wrapper failed: {str(e)}")

    @staticmethod
    async def _sync_amazon_orders_wrapper(amazon_service, seller_id: str):
        """Wrapper para ejecutar Amazon sync."""
        try:
            logger.info(f"Executing Amazon sync for {seller_id}")
            result = await amazon_service.sync_orders()
            logger.info(f"Amazon sync complete")
        except Exception as e:
            logger.error(f"Amazon sync wrapper failed: {str(e)}")

    @staticmethod
    async def _sync_shopify_orders_wrapper(shopify_service, store_url: str):
        """Wrapper para ejecutar Shopify sync."""
        try:
            logger.info(f"Executing Shopify sync for {store_url}")
            result = await shopify_service.sync_orders()
            logger.info(f"Shopify sync complete")
        except Exception as e:
            logger.error(f"Shopify sync wrapper failed: {str(e)}")
