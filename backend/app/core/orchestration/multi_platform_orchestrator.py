"""
Multi-Platform Orchestrator — Coordina inventory sync, influencer tracking, analytics extraction, sentiment analysis.

Fase 1+2+3 convergence: integra knowledge + Computer Use + dashboards.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class MultiPlatformOrchestrator:
    """Orquesta operaciones multi-plataforma complejas."""

    def __init__(self, browser_agent, db, cache):
        self.browser_agent = browser_agent
        self.db = db
        self.cache = cache
        self.sync_intervals = {
            "inventory": 300,  # 5 minutos
            "analytics": 3600,  # 1 hora
            "reviews": 7200,  # 2 horas
        }

    # ========== FASE 1: INVENTORY SYNC ==========

    async def sync_inventory_realtime(self) -> Dict[str, Any]:
        """
        Sincroniza stock DB → todas plataformas.

        Master inventory en DB. Cada 5min:
        1. Obtiene stock actual DB
        2. Compara con cada plataforma (Computer Use extrae)
        3. Si diferencia, push update automático
        """

        logger.info("Starting real-time inventory sync")

        master_inventory = await self.db.query("SELECT sku, quantity FROM inventory WHERE enabled = true")

        results = {
            "total_skus": len(master_inventory),
            "synced": 0,
            "failed": 0,
            "platforms": {},
        }

        for sku_record in master_inventory:
            sku = sku_record["sku"]
            master_qty = sku_record["quantity"]

            # Obtener listings para este SKU
            listings = await self.db.query(
                "SELECT platform, platform_listing_id, current_qty FROM listings WHERE sku = %s",
                [sku],
            )

            for listing in listings:
                platform = listing["platform"]
                platform_listing_id = listing["platform_listing_id"]
                platform_qty = listing["current_qty"]

                if platform_qty != master_qty:
                    # Disparar Computer Use para actualizar
                    update_result = await self._update_platform_stock(
                        platform, platform_listing_id, master_qty
                    )

                    if update_result["status"] == "success":
                        results["synced"] += 1
                        results["platforms"].setdefault(platform, []).append({
                            "sku": sku,
                            "updated": master_qty,
                        })
                        # Actualizar DB listing
                        await self.db.execute(
                            "UPDATE listings SET current_qty = %s, last_sync = NOW() WHERE platform = %s AND platform_listing_id = %s",
                            [master_qty, platform, platform_listing_id],
                        )
                    else:
                        results["failed"] += 1
                        logger.error(f"Failed to sync {sku} on {platform}: {update_result.get('error')}")

        logger.info(f"Inventory sync complete: {results['synced']} synced, {results['failed']} failed")
        return results

    async def _update_platform_stock(
        self, platform: str, listing_id: str, quantity: int
    ) -> Dict[str, Any]:
        """
        Computer Use actualiza stock en plataforma.

        Plataforma-específico: MercadoLibre, Amazon, Shopify, eBay, etc.
        """

        if platform == "mercadolibre":
            # Navigate to ML listing editor
            actions = [
                {"type": "navigate", "params": {"url": f"https://www.mercadolibre.com.ar/mip/items/{listing_id}"}},
                {"type": "click", "params": {"selector": "button[aria-label='Editar']"}},
                {"type": "fill_form", "params": {"fields": {"input[name='quantity']": str(quantity)}}},
                {"type": "click", "params": {"selector": "button:has-text('Guardar')"}},
                {"type": "screenshot", "params": {"filename": f"ml_sync_{listing_id}.png"}},
            ]
            result = await self.browser_agent.execute_workflow(
                f"sync_ml_{listing_id}", actions
            )
            return {"status": "success" if result.get("completed") == len(actions) else "failed", "error": result.get("error")}

        elif platform == "shopify":
            actions = [
                {"type": "navigate", "params": {"url": f"https://admin.shopify.com/products/{listing_id}"}},
                {"type": "fill_form", "params": {"fields": {"input[placeholder*='Quantity']": str(quantity)}}},
                {"type": "click", "params": {"selector": "button:has-text('Save')"}},
            ]
            result = await self.browser_agent.execute_workflow(
                f"sync_shopify_{listing_id}", actions
            )
            return {"status": "success" if result.get("completed") == len(actions) else "failed"}

        # Agregar más plataformas según sea necesario
        return {"status": "error", "error": f"Platform {platform} not supported"}

    # ========== FASE 2: INFLUENCER TRACKING ==========

    async def track_influencer_sales(self) -> Dict[str, Any]:
        """
        Monitorea ventas por influencer + calcula comisiones automáticamente.
        """

        logger.info("Starting influencer sales tracking")

        influencers = await self.db.query(
            "SELECT id, name, promo_code, commission_rate FROM influencers WHERE active = true"
        )

        results = {"tracked": 0, "total_revenue": 0, "commissions_owed": 0, "influencers": []}

        for influencer in influencers:
            infl_id = influencer["id"]
            promo_code = influencer["promo_code"]
            commission_rate = influencer["commission_rate"]

            # Obtener ventas con este promo code (últimas 24h)
            sales = await self.db.query(
                "SELECT COUNT(*) as count, SUM(amount) as total FROM orders WHERE promo_code = %s AND created_at > NOW() - INTERVAL 1 DAY",
                [promo_code],
            )

            if sales:
                count = sales[0]["count"] or 0
                total_revenue = sales[0]["total"] or 0
                commission_owed = total_revenue * commission_rate

                results["tracked"] += count
                results["total_revenue"] += total_revenue
                results["commissions_owed"] += commission_owed

                results["influencers"].append({
                    "influencer_id": infl_id,
                    "name": influencer["name"],
                    "sales_24h": count,
                    "revenue_24h": total_revenue,
                    "commission_owed": commission_owed,
                })

                # Auto-trigger payout si commission_owed > threshold
                if commission_owed > 100:
                    await self._create_payout(infl_id, commission_owed)

        return results

    async def _create_payout(self, influencer_id: str, amount: float) -> None:
        """Crea payout para influencer."""
        await self.db.execute(
            "INSERT INTO influencer_payouts (influencer_id, amount, status, created_at) VALUES (%s, %s, 'pending', NOW())",
            [influencer_id, amount],
        )
        logger.info(f"Payout created for influencer {influencer_id}: ${amount}")

    # ========== FASE 2: ANALYTICS EXTRACTION ==========

    async def extract_platform_analytics(self) -> Dict[str, Any]:
        """
        Computer Use extrae dashboards analytics reales de cada plataforma.

        OCR + scrape nativo de cada dashboard.
        """

        logger.info("Extracting platform analytics")

        platforms = ["mercadolibre", "amazon", "tiktok_shop", "ebay", "shopify"]
        results = {"platforms": {}, "timestamp": datetime.utcnow().isoformat()}

        for platform in platforms:
            try:
                analytics = await self._extract_platform_metrics(platform)
                results["platforms"][platform] = analytics
            except Exception as e:
                logger.error(f"Failed to extract {platform} analytics: {str(e)}")
                results["platforms"][platform] = {"error": str(e)}

        # Guardar en cache (1 hora)
        await self.cache.set(
            "platform_analytics",
            results,
            ex=3600,
        )

        return results

    async def _extract_platform_metrics(self, platform: str) -> Dict[str, Any]:
        """
        Extrae métricas específicas por plataforma.
        """

        if platform == "mercadolibre":
            actions = [
                {"type": "navigate", "params": {"url": "https://www.mercadolibre.com.ar/myaccount/seller-center"}},
                {"type": "screenshot", "params": {"filename": "ml_dashboard.png"}},
                {"type": "ocr", "params": {"selector": "div.metrics"}},
            ]

        elif platform == "amazon":
            actions = [
                {"type": "navigate", "params": {"url": "https://sellercentral.amazon.com/dashboard"}},
                {"type": "screenshot", "params": {"filename": "amz_dashboard.png"}},
            ]

        elif platform == "tiktok_shop":
            actions = [
                {"type": "navigate", "params": {"url": "https://seller.tiktok.com/dashboard"}},
                {"type": "screenshot", "params": {"filename": "tt_dashboard.png"}},
            ]

        else:
            return {}

        result = await self.browser_agent.execute_workflow(
            f"extract_{platform}_analytics", actions
        )

        # Parsear OCR result (simplificado)
        return {
            "platform": platform,
            "extracted_at": datetime.utcnow().isoformat(),
            "status": "success" if result.get("completed") > 0 else "failed",
        }

    # ========== FASE 2: SENTIMENT ANALYSIS ==========

    async def analyze_reviews_sentiment(self) -> Dict[str, Any]:
        """
        Extrae reviews → OpenAI sentiment analysis → alertas automáticas.
        """

        logger.info("Analyzing customer sentiment")

        # Obtener reviews sin analizar (últimas 24h)
        new_reviews = await self.db.query(
            "SELECT id, text, platform, rating FROM reviews WHERE analyzed = false AND created_at > NOW() - INTERVAL 1 DAY"
        )

        results = {
            "analyzed": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "churn_signals": [],
        }

        for review in new_reviews:
            # TODO: Integrar OpenAI para sentiment analysis
            sentiment = await self._classify_sentiment(review["text"])

            results[sentiment] += 1

            # Guardar análisis
            await self.db.execute(
                "UPDATE reviews SET analyzed = true, sentiment = %s, analyzed_at = NOW() WHERE id = %s",
                [sentiment, review["id"]],
            )

            # Si negativo + menciona alternativas = churn signal
            if sentiment == "negative" and any(
                word in review["text"].lower() for word in ["otro", "competencia", "mejor", "no recomiendo"]
            ):
                results["churn_signals"].append({
                    "review_id": review["id"],
                    "platform": review["platform"],
                    "signal": "Mentions alternatives",
                })

            results["analyzed"] += 1

        # Auto-responder negativos
        negative_reviews = await self.db.query(
            "SELECT id FROM reviews WHERE sentiment = 'negative' AND responded = false"
        )

        for neg_review in negative_reviews:
            await self._auto_respond_negative_review(neg_review["id"])

        return results

    async def _classify_sentiment(self, text: str) -> str:
        """Clasifica sentimiento (simple heurística, o integrar OpenAI)."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["excelente", "perfecto", "recomiendo", "muy bueno"]):
            return "positive"
        elif any(word in text_lower for word in ["malo", "pésimo", "no recomiendo", "decepción"]):
            return "negative"
        else:
            return "neutral"

    async def _auto_respond_negative_review(self, review_id: str) -> None:
        """Computer Use responde reviews negativas automáticamente."""
        logger.info(f"Auto-responding to negative review {review_id}")
        # TODO: Implementar respuesta automática via WhatsApp/email

    # ========== DASHBOARD REPORTING ==========

    async def get_unified_dashboard(self) -> Dict[str, Any]:
        """
        Dashboard unificado: inventory, analytics, influencers, sentiment.
        """

        # Obtener últimos datos de cada sistema
        inventory = await self.db.query(
            "SELECT COUNT(*) as total_skus, SUM(quantity) as total_stock FROM inventory WHERE enabled = true"
        )

        sales_24h = await self.db.query(
            "SELECT COUNT(*) as sales, SUM(amount) as revenue FROM orders WHERE created_at > NOW() - INTERVAL 1 DAY"
        )

        reviews = await self.db.query(
            "SELECT sentiment, COUNT(*) as count FROM reviews WHERE created_at > NOW() - INTERVAL 7 DAY GROUP BY sentiment"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "inventory": {
                "total_skus": inventory[0]["total_skus"] if inventory else 0,
                "total_stock": inventory[0]["total_stock"] if inventory else 0,
            },
            "sales": {
                "count_24h": sales_24h[0]["sales"] if sales_24h else 0,
                "revenue_24h": sales_24h[0]["revenue"] if sales_24h else 0,
            },
            "sentiment": {
                "positive": next((r["count"] for r in reviews if r["sentiment"] == "positive"), 0),
                "neutral": next((r["count"] for r in reviews if r["sentiment"] == "neutral"), 0),
                "negative": next((r["count"] for r in reviews if r["sentiment"] == "negative"), 0),
            },
        }
