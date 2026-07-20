"""
Competitive Intelligence Engine

Sistema de espionaje 24/7 que monitorea competidores, detecta cambios de precios
y promociones, y sugiere estrategias de respuesta con IA.
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.alerts.models import Alert, AlertSeverity, AlertStatus
from app.domains.catalogs.models import CatalogItem
from app.domains.competitive.models import CompetitiveMonitor

logger = get_logger(__name__)

# Regex para extraer precios de HTML/texto
_PRICE_PATTERNS = [
    re.compile(r'\$\s*([\d.,]+)', re.IGNORECASE),
    re.compile(r'([\d.,]+)\s*(?:USD|ARS|USD\$|ARS\$)', re.IGNORECASE),
    re.compile(r'precio[:\s]*\$?\s*([\d.,]+)', re.IGNORECASE),
    re.compile(r'([\d.,]+)\s*pesos', re.IGNORECASE),
]

# Regex para detectar promociones
_PROMO_PATTERNS = [
    re.compile(r'2x1', re.IGNORECASE),
    re.compile(r'50%\s*off', re.IGNORECASE),
    re.compile(r'descuento\s+del?\s+\d+%', re.IGNORECASE),
    re.compile(r'promo', re.IGNORECASE),
    re.compile(r'oferta', re.IGNORECASE),
    re.compile(r'envio\s+gratis', re.IGNORECASE),
    re.compile(r'cuotas?\s+sin\s+interes', re.IGNORECASE),
]


def _extract_prices(text: str) -> Dict[str, str]:
    """Extrae precios de texto crudo usando regex."""
    prices: Dict[str, str] = {}
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for pattern in _PRICE_PATTERNS:
            matches = pattern.findall(line)
            if matches:
                # Usar la linea como clave aproximada del producto
                key = line[:80].strip()
                for m in matches:
                    prices[key] = m.replace('.', '').replace(',', '.')
                break
    return prices


def _detect_promotions(text: str) -> List[str]:
    """Detecta menciones a promociones en el texto."""
    promos: List[str] = []
    for pattern in _PROMO_PATTERNS:
        if pattern.search(text):
            promos.append(pattern.pattern)
    return promos


def _normalize_price(value: str) -> Optional[float]:
    """Normaliza un string de precio a float."""
    try:
        cleaned = value.replace('$', '').replace(' ', '').replace(',', '.')
        # Manejar miles con punto
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        return float(cleaned)
    except Exception:
        return None


class CompetitiveIntelligenceEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def monitor_competitor(
        self,
        business_id: uuid.UUID,
        competitor_url: str,
        competitor_name: str,
        products_to_track: Optional[List[str]] = None,
    ) -> CompetitiveMonitor:
        """Registra un competidor para monitoreo continuo."""
        monitor = CompetitiveMonitor(
            business_id=business_id,
            competitor_name=competitor_name,
            competitor_url=competitor_url,
            products_to_track=products_to_track or [],
            status='active',
        )
        self.db.add(monitor)
        await self.db.commit()
        await self.db.refresh(monitor)
        logger.info(f"Monitor creado: {competitor_name} para business {business_id}")
        return monitor

    async def scrape_competitor(self, monitor_id: uuid.UUID) -> Dict[str, Any]:
        """Scrapea el sitio del competidor y extrae precios."""
        result = await self.db.execute(
            select(CompetitiveMonitor).where(CompetitiveMonitor.id == monitor_id)
        )
        monitor = result.scalar_one_or_none()
        if not monitor:
            return {"error": "Monitor no encontrado"}

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-AR,es;q=0.9",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(monitor.competitor_url)
                resp.raise_for_status()
                text = resp.text

            prices = _extract_prices(text)
            promos = _detect_promotions(text)

            snapshot = {
                "prices": prices,
                "promotions": promos,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            monitor.last_scraped_at = datetime.now(timezone.utc)
            monitor.last_snapshot = snapshot
            monitor.status = 'active'
            await self.db.commit()

            logger.info(f"Scrape exitoso: {monitor.competitor_name} — {len(prices)} precios, {len(promos)} promos")
            return {
                "monitor_id": monitor_id,
                "prices_found": prices,
                "promotions_found": promos,
                "scraped_at": snapshot["scraped_at"],
                "status": "ok",
            }
        except httpx.HTTPStatusError as e:
            monitor.status = 'error'
            await self.db.commit()
            logger.error(f"Scrape HTTP error {monitor.competitor_url}: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}", "status": "error"}
        except Exception as e:
            monitor.status = 'error'
            await self.db.commit()
            logger.error(f"Scrape error {monitor.competitor_url}: {e}")
            return {"error": str(e), "status": "error"}

    async def detect_changes(self, business_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Compara el ultimo snapshot con el anterior y detecta cambios."""
        result = await self.db.execute(
            select(CompetitiveMonitor)
            .where(
                CompetitiveMonitor.business_id == business_id,
                CompetitiveMonitor.status == 'active',
            )
        )
        monitors = result.scalars().all()
        changes: List[Dict[str, Any]] = []

        for monitor in monitors:
            snapshot = monitor.last_snapshot or {}
            if not snapshot:
                continue

            prev_snapshot = snapshot.get("previous", {})
            current_prices = snapshot.get("prices", {})
            prev_prices = prev_snapshot.get("prices", {})

            # Guardar snapshot actual como previo para la proxima corrida
            monitor.last_snapshot = {
                **snapshot,
                "previous": snapshot,
            }
            await self.db.commit()

            for product, price_str in current_prices.items():
                current_price = _normalize_price(price_str)
                prev_price_str = prev_prices.get(product)
                prev_price = _normalize_price(prev_price_str) if prev_price_str else None

                if current_price is None:
                    continue

                if prev_price is None:
                    changes.append({
                        "change_type": "new_product",
                        "severity": "info",
                        "competitor_name": monitor.competitor_name,
                        "product_name": product,
                        "old_value": None,
                        "new_value": price_str,
                        "diff_percent": None,
                        "detected_at": datetime.now(timezone.utc),
                    })
                    continue

                if current_price < prev_price:
                    diff = ((prev_price - current_price) / prev_price) * 100 if prev_price else 0
                    severity = "critical" if diff > 20 else "warning"
                    changes.append({
                        "change_type": "price_down",
                        "severity": severity,
                        "competitor_name": monitor.competitor_name,
                        "product_name": product,
                        "old_value": prev_price_str,
                        "new_value": price_str,
                        "diff_percent": round(diff, 2),
                        "detected_at": datetime.now(timezone.utc),
                    })
                elif current_price > prev_price:
                    diff = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
                    changes.append({
                        "change_type": "price_up",
                        "severity": "info",
                        "competitor_name": monitor.competitor_name,
                        "product_name": product,
                        "old_value": prev_price_str,
                        "new_value": price_str,
                        "diff_percent": round(diff, 2),
                        "detected_at": datetime.now(timezone.utc),
                    })

            # Detectar nuevas promociones
            current_promos = set(snapshot.get("promotions", []))
            prev_promos = set(prev_snapshot.get("promotions", []))
            new_promos = current_promos - prev_promos
            for promo in new_promos:
                changes.append({
                    "change_type": "promo_started",
                    "severity": "warning",
                    "competitor_name": monitor.competitor_name,
                    "product_name": None,
                    "old_value": None,
                    "new_value": promo,
                    "diff_percent": None,
                    "detected_at": datetime.now(timezone.utc),
                })

            # Detectar productos fuera de stock (desaparecidos del snapshot)
            gone_products = set(prev_prices.keys()) - set(current_prices.keys())
            for product in gone_products:
                changes.append({
                    "change_type": "out_of_stock",
                    "severity": "info",
                    "competitor_name": monitor.competitor_name,
                    "product_name": product,
                    "old_value": prev_prices.get(product),
                    "new_value": None,
                    "diff_percent": None,
                    "detected_at": datetime.now(timezone.utc),
                })

        return changes

    async def generate_response_strategy(
        self,
        business_id: uuid.UUID,
        change: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Usa IA para sugerir una estrategia de respuesta ante un cambio competitivo."""
        try:
            from app.domains.agents.ai_reply import generate_raw_ai_response

            competitor = change.get("competitor_name", "Competidor")
            change_type = change.get("change_type", "cambio")
            product = change.get("product_name", "producto")
            diff = change.get("diff_percent", 0)

            system_prompt = (
                "Sos un analista de inteligencia competitiva de SellIA. "
                "Tu trabajo es proponer estrategias de respuesta ante movimientos de la competencia. "
                "Sé conciso, accionable y mencioná riesgos. Respondé en español argentino."
            )
            user_prompt = (
                f"El competidor '{competitor}' realizó un cambio: {change_type} "
                f"sobre '{product}'. Diferencia: {diff}%.\n\n"
                "Proponé una estrategia con 4 opciones numeradas y un riesgo clave."
            )

            suggestion = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=400,
                temperature=0.7,
            )

            # Parseo simple para extraer opciones
            options: List[str] = []
            risk_note = None
            if suggestion:
                lines = suggestion.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith(('1.', '2.', '3.', '4.')):
                        options.append(stripped)
                    elif 'riesgo' in stripped.lower() or 'risk' in stripped.lower():
                        risk_note = stripped

            return {
                "change": change,
                "suggestion": suggestion or "No se pudo generar sugerencia.",
                "options": options if options else ["Evaluar manualmente"],
                "risk_note": risk_note,
            }
        except Exception as e:
            logger.error(f"Error generando estrategia: {e}")
            return {
                "change": change,
                "suggestion": "Recomendacion: Ofrecer bundle con mayor valor percibido",
                "options": [
                    "Igualar precio (riesgo: erosion de margen)",
                    "Ofrecer bundle con mayor valor percibido",
                    "Destacar diferenciacion propia",
                    "No hacer nada (si la lealtad de marca es fuerte)",
                ],
                "risk_note": "Riesgo de matching: Erosion de margen 15%",
            }

    async def get_intelligence_dashboard(self, business_id: uuid.UUID) -> Dict[str, Any]:
        """Retorna todo el estado de inteligencia competitiva para un negocio."""
        result = await self.db.execute(
            select(CompetitiveMonitor)
            .where(CompetitiveMonitor.business_id == business_id)
            .order_by(desc(CompetitiveMonitor.created_at))
        )
        monitors = result.scalars().all()

        # Alertas recientes del tipo competidor
        alert_result = await self.db.execute(
            select(Alert)
            .where(
                Alert.business_id == business_id,
                Alert.title.ilike("%competidor%"),
            )
            .order_by(desc(Alert.created_at))
            .limit(20)
        )
        alerts = alert_result.scalars().all()

        unread = sum(1 for a in alerts if a.status == AlertStatus.UNREAD)

        # Detectar cambios recientes
        changes = await self.detect_changes(business_id)

        # Generar estrategias para cambios criticos/warning
        strategies = []
        for change in changes[:3]:
            if change.get("severity") in ("critical", "warning"):
                strategy = await self.generate_response_strategy(business_id, change)
                strategies.append(strategy)

        return {
            "monitors": monitors,
            "recent_changes": changes,
            "alerts_count": len(alerts),
            "unread_alerts": unread,
            "strategies": strategies,
        }

    async def create_alert(self, business_id: uuid.UUID, change: Dict[str, Any]) -> Alert:
        """Crea una alerta en el sistema para notificar al usuario."""
        change_type = change.get("change_type", "cambio")
        competitor = change.get("competitor_name", "Competidor")
        product = change.get("product_name", "")
        diff = change.get("diff_percent")

        title_map = {
            "price_down": f"Competidor {competitor} bajo precio",
            "price_up": f"Competidor {competitor} subio precio",
            "new_product": f"Competidor {competitor} lanzo nuevo producto",
            "promo_started": f"Competidor {competitor} inicio promocion",
            "out_of_stock": f"Competidor {competitor} quedo sin stock",
        }
        title = title_map.get(change_type, f"Cambio detectado en {competitor}")

        description_parts = [f"Cambio: {change_type}"]
        if product:
            description_parts.append(f"Producto: {product}")
        if diff is not None:
            description_parts.append(f"Diferencia: {diff}%")

        severity_map = {
            "critical": AlertSeverity.CRITICAL,
            "warning": AlertSeverity.WARNING,
            "info": AlertSeverity.INFO,
        }
        severity = severity_map.get(change.get("severity", "info"), AlertSeverity.INFO)

        alert = Alert(
            business_id=business_id,
            title=title,
            description=". ".join(description_parts),
            severity=severity,
            status=AlertStatus.UNREAD,
            entity_type="competitor",
            alert_metadata=change,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info(f"Alerta creada: {title} para business {business_id}")
        return alert
