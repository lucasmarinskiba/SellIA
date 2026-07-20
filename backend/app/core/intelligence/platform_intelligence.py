"""
Platform Intelligence Engine — SellIA entiende todas plataformas.

Registro de 6+ plataformas:
- Mercado Libre (LatAm, 10% comisión)
- Amazon (global, 15% comisión)
- Hotmart (digitales, 50% comisión)
- Beacons (link aggregator, venta directa)
- TiendaNube (tienda propia LatAm)
- Shopify (tienda propia global)

Cada plataforma: comisiones, límites, audiencia, API, shipping, conversion rate.
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Platform:
    name: str
    commission_rate: float
    min_order: float
    max_order: float
    audience_size: int
    conversion_rate: float
    best_for: str


class PlatformIntelligence:
    """Motor de inteligencia de plataformas."""

    PLATFORMS = {
        "mercado_libre": Platform(
            name="Mercado Libre",
            commission_rate=0.10,
            min_order=0,
            max_order=999999,
            audience_size=1_000_000,
            conversion_rate=0.045,
            best_for="Físicos LatAm",
        ),
        "amazon": Platform(
            name="Amazon",
            commission_rate=0.15,
            min_order=5,
            max_order=50000,
            audience_size=100_000_000,
            conversion_rate=0.08,
            best_for="Electrónica global",
        ),
        "hotmart": Platform(
            name="Hotmart",
            commission_rate=0.50,
            min_order=1,
            max_order=9999,
            audience_size=5_000_000,
            conversion_rate=0.02,
            best_for="Cursos/digitales",
        ),
        "beacons": Platform(
            name="Beacons",
            commission_rate=0.05,
            min_order=0,
            max_order=999999,
            audience_size=500_000,
            conversion_rate=0.05,
            best_for="Link agregador",
        ),
        "tienda_nube": Platform(
            name="TiendaNube",
            commission_rate=0.05,
            min_order=0,
            max_order=999999,
            audience_size=100_000,
            conversion_rate=0.04,
            best_for="Tienda propia LatAm",
        ),
        "shopify": Platform(
            name="Shopify",
            commission_rate=0.029,
            min_order=0,
            max_order=999999,
            audience_size=1_000_000,
            conversion_rate=0.03,
            best_for="Tienda propia global",
        ),
    }

    async def analyze_product(
        self,
        product_name: str,
        price: float,
        product_type: str,
    ) -> Dict[str, Any]:
        """Recomienda mejores plataformas para producto."""

        logger.info(f"Analyzing {product_name}")

        scores = {}
        for pid, platform in self.PLATFORMS.items():
            score = 50  # Base

            if platform.min_order <= price <= platform.max_order:
                score += 20

            if product_type == "digital" and "digital" in platform.best_for.lower():
                score += 30
            elif product_type == "physical" and ("LatAm" in platform.best_for or "global" in platform.best_for):
                score += 30

            if platform.commission_rate < 0.15:
                score += 10

            scores[pid] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "status": "success",
            "product": product_name,
            "recommendations": [
                {
                    "platform": self.PLATFORMS[pid].name,
                    "score": score,
                    "commission": f"{self.PLATFORMS[pid].commission_rate * 100:.1f}%",
                }
                for pid, score in ranked
            ],
        }
