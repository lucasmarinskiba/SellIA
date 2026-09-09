"""The statistics a real analyst would insist on before reading a number aloud.

A dashboard that says "conversión 33%" off three conversations is worse than
one that says nothing: the user changes their business over noise. Everything
here exists to keep a number attached to how much evidence is behind it.

No third-party stats package: the two things needed (a Wilson interval for a
proportion, a median for a latency) are a few lines each, and adding scipy to
the Railway image for them is not a trade worth making.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

Z_95 = 1.959963984540054

# Sample-size bands. These are conventions, not laws, and are stated as such in
# the copy the user reads -- the point is to stop a 2-of-3 fluke from being
# presented with the same confidence as a 200-of-300 result.
MIN_TO_READ = 5
MIN_FOR_TREND = 30


@dataclass
class Proportion:
    """A rate, with the interval it could really be hiding."""

    successes: int
    total: int

    @property
    def rate(self) -> float:
        return (self.successes / self.total) if self.total else 0.0

    @property
    def percent(self) -> float:
        return round(self.rate * 100, 1)

    def wilson_interval(self, z: float = Z_95) -> tuple[float, float]:
        """95% Wilson score interval — correct for the small samples this app
        actually has, unlike the normal approximation, which happily returns
        negative lower bounds when n is tiny."""
        n = self.total
        if n == 0:
            return (0.0, 0.0)
        p = self.rate
        denom = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denom
        margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
        return (round(max(0.0, center - margin) * 100, 1), round(min(1.0, center + margin) * 100, 1))

    @property
    def confidence(self) -> str:
        if self.total < MIN_TO_READ:
            return "insufficient"
        if self.total < MIN_FOR_TREND:
            return "preliminary"
        return "solid"

    def reading(self, subject: str) -> str:
        """What an analyst would actually say about this rate."""
        low, high = self.wilson_interval()
        if self.total == 0:
            return f"Todavía no hay {subject} para medir."
        if self.total < MIN_TO_READ:
            return (
                f"{self.successes} de {self.total} {subject}. Con una muestra tan chica el "
                f"porcentaje no significa nada todavía: podría estar entre {low}% y {high}%."
            )
        if self.total < MIN_FOR_TREND:
            return (
                f"{self.percent}% ({self.successes} de {self.total} {subject}). Es una lectura "
                f"preliminar: el valor real está entre {low}% y {high}%."
            )
        return (
            f"{self.percent}% ({self.successes} de {self.total} {subject}), con un margen real "
            f"de {low}% a {high}%."
        )


def median(values: Sequence[float]) -> Optional[float]:
    """Median, not mean: one customer answered three days late would drag an
    average past the point of being descriptive."""
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def quartiles(values: Sequence[float]) -> tuple[Optional[float], Optional[float]]:
    if len(values) < 4:
        return (None, None)
    ordered = sorted(values)
    mid = len(ordered) // 2
    lower = ordered[:mid]
    upper = ordered[mid + 1:] if len(ordered) % 2 else ordered[mid:]
    return (median(lower), median(upper))


def describe_change(current: int, previous: int, unit: str) -> dict[str, object]:
    """Week-over-week style comparison that refuses to dramatise small counts."""
    delta = current - previous
    if previous == 0 and current == 0:
        return {"direction": "flat", "delta": 0, "percent": None,
                "reading": f"Sin {unit} en ninguno de los dos períodos."}
    if previous == 0:
        return {"direction": "up", "delta": delta, "percent": None,
                "reading": f"Pasaste de 0 a {current} {unit}: es el primer período con actividad, "
                           f"todavía no hay con qué compararlo."}
    percent = round((current - previous) / previous * 100, 1)
    direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
    if current + previous < MIN_TO_READ * 2:
        reading = (
            f"{current} vs {previous} {unit}. Son números chicos: una diferencia de {abs(delta)} "
            f"puede ser simple azar, no una tendencia."
        )
    else:
        verb = "subió" if delta > 0 else "bajó" if delta < 0 else "quedó igual"
        reading = f"{verb} {abs(percent)}% ({current} vs {previous} {unit})."
    return {"direction": direction, "delta": delta, "percent": percent, "reading": reading}
