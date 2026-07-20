"""Computer Use — Auto Healer

Cuando un selector falla o una acción no tiene efecto, intenta
encontrar alternativas automáticamente: buscar por texto similar,
usar atributos ARIA, o fallback a coordenadas cercanas.
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HealResult:
    success: bool
    new_selector: Optional[str]
    new_coords: Optional[Dict[str, int]]
    strategy: str
    confidence: float


class AutoHealer:
    """Sistema de auto-recuperación para acciones fallidas."""

    async def heal_click(
        self,
        page,
        original_x: int,
        original_y: int,
        expected_text: Optional[str] = None,
    ) -> HealResult:
        """Intenta recuperar un click fallido."""
        strategies = []

        # Strategy 1: Find element by expected text near coordinates
        if expected_text:
            try:
                element = await page.query_selector(f"text={expected_text}")
                if element:
                    box = await element.bounding_box()
                    if box:
                        return HealResult(
                            success=True,
                            new_selector=f"text={expected_text}",
                            new_coords={"x": int(box["x"] + box["width"] / 2), "y": int(box["y"] + box["height"] / 2)},
                            strategy="text_match",
                            confidence=0.9,
                        )
            except Exception:
                pass

        # Strategy 2: Look for interactive elements near original coords
        try:
            elements = await page.query_selector_all("button, a, input, [role='button'], [onclick]")
            closest = None
            closest_dist = float("inf")
            for el in elements:
                box = await el.bounding_box()
                if box:
                    cx = box["x"] + box["width"] / 2
                    cy = box["y"] + box["height"] / 2
                    dist = ((cx - original_x) ** 2 + (cy - original_y) ** 2) ** 0.5
                    if dist < closest_dist and dist < 200:  # Within 200px
                        closest_dist = dist
                        closest = el

            if closest:
                box = await closest.bounding_box()
                return HealResult(
                    success=True,
                    new_selector=None,
                    new_coords={"x": int(box["x"] + box["width"] / 2), "y": int(box["y"] + box["height"] / 2)},
                    strategy="nearby_element",
                    confidence=max(0, 1 - closest_dist / 200),
                )
        except Exception:
            pass

        # Strategy 3: Try slight offset
        offsets = [(10, 0), (-10, 0), (0, 10), (0, -10), (20, 20), (-20, -20)]
        for dx, dy in offsets:
            try:
                # Just verify coordinates are within viewport
                viewport = await page.viewport_size()
                new_x = max(0, min(original_x + dx, viewport["width"] - 1))
                new_y = max(0, min(original_y + dy, viewport["height"] - 1))
                return HealResult(
                    success=True,
                    new_selector=None,
                    new_coords={"x": new_x, "y": new_y},
                    strategy="offset",
                    confidence=0.3,
                )
            except Exception:
                continue

        return HealResult(
            success=False,
            new_selector=None,
            new_coords=None,
            strategy="exhausted",
            confidence=0.0,
        )

    async def heal_type(
        self,
        page,
        original_selector: Optional[str] = None,
    ) -> HealResult:
        """Intenta recuperar un typing fallido encontrando un input enfocable."""
        try:
            # Find first visible input
            inputs = await page.query_selector_all("input, textarea, [contenteditable='true']")
            for inp in inputs:
                if await inp.is_visible() and await inp.is_enabled():
                    box = await inp.bounding_box()
                    return HealResult(
                        success=True,
                        new_selector=None,
                        new_coords={"x": int(box["x"] + box["width"] / 2), "y": int(box["y"] + box["height"] / 2)} if box else None,
                        strategy="first_input",
                        confidence=0.6,
                    )
        except Exception:
            pass

        return HealResult(success=False, new_selector=None, new_coords=None, strategy="exhausted", confidence=0.0)

    async def heal_navigate(
        self,
        page,
        original_url: str,
    ) -> HealResult:
        """Intenta recuperar una navegación fallida."""
        # Try www. prefix
        if not original_url.startswith("www.") and "//" in original_url:
            parts = original_url.split("//", 1)
            new_url = f"{parts[0]}//www.{parts[1]}"
            return HealResult(
                success=True,
                new_selector=None,
                new_coords=None,
                strategy="www_prefix",
                confidence=0.4,
            )

        # Try http vs https
        if original_url.startswith("https://"):
            new_url = original_url.replace("https://", "http://", 1)
            return HealResult(
                success=True,
                new_selector=None,
                new_coords=None,
                strategy="http_fallback",
                confidence=0.3,
            )

        return HealResult(success=False, new_selector=None, new_coords=None, strategy="exhausted", confidence=0.0)

    def get_heal_summary(self, heals: List[HealResult]) -> Dict[str, Any]:
        """Resumen de recuperaciones."""
        successful = [h for h in heals if h.success]
        return {
            "total_attempts": len(heals),
            "successful": len(successful),
            "strategies_used": list(set(h.strategy for h in successful)),
            "avg_confidence": sum(h.confidence for h in successful) / len(successful) if successful else 0,
        }
