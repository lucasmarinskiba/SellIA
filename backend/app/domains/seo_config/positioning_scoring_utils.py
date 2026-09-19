"""Platform-agnostic scoring helpers shared by link-level and store-level
positioning services. Pure functions — no DB access, no platform knowledge."""

from app.domains.seo_config.platform_ranking_base import RankingSignal


def composite_from_sub_scores(sub_scores: dict[str, float | None]) -> float:
    """Simple mean of non-null sub-scores.

    Without ML/Amazon/Meta publishing exact ranking weights, an unweighted
    mean over available *measured* pillars is the defensible default —
    inventing decimal weights would be false precision. Pillars with no
    honest signal are None and are excluded, not counted as zero.
    """
    values = [v for v in sub_scores.values() if v is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)


def measured_pct(signals: list[RankingSignal]) -> float:
    """Share of signals with measured=True — a trust indicator so a score
    built mostly from heuristic/unmeasured signals reads as such."""
    if not signals:
        return 0.0
    measured = sum(1 for s in signals if s.measured)
    return round(measured / len(signals) * 100, 1)
