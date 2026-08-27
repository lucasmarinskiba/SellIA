"""Hierarchical reconciliation.

Bottom-up: child forecasts (per SKU / per channel) are the source of truth
for shape; the total is scaled to their sum. When a trustworthy top-level
forecast exists (lower backtest WAPE), we instead nudge children toward
the top with a proportional (`top-down`) split. `blend` mixes the two by a
weight derived from relative backtest accuracy — a lightweight stand-in
for MinT that needs no covariance estimate.
"""

from __future__ import annotations

import numpy as np


def bottom_up(child_paths: list[np.ndarray]) -> np.ndarray:
    if not child_paths:
        return np.array([])
    h = min(len(p) for p in child_paths)
    return np.sum([np.asarray(p[:h], dtype=float) for p in child_paths], axis=0)


def top_down(total_path: np.ndarray, child_paths: list[np.ndarray]) -> list[np.ndarray]:
    total_path = np.asarray(total_path, dtype=float)
    h = min([len(total_path)] + [len(p) for p in child_paths])
    stacked = np.vstack([np.asarray(p[:h], dtype=float) for p in child_paths])
    denom = stacked.sum(axis=0)
    denom = np.where(denom <= 1e-9, 1.0, denom)
    share = stacked / denom
    return [share[i] * total_path[:h] for i in range(len(child_paths))]


def reconcile(
    total_path: np.ndarray | None,
    child_paths: list[np.ndarray],
    total_wape: float | None = None,
    child_wapes: list[float] | None = None,
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Return a coherent (total == sum(children)) set of paths."""
    if not child_paths:
        return (np.asarray(total_path, dtype=float) if total_path is not None else np.array([])), []

    bu = bottom_up(child_paths)
    if total_path is None:
        return bu, [np.asarray(p[: len(bu)], dtype=float) for p in child_paths]

    total_path = np.asarray(total_path, dtype=float)[: len(bu)]

    # weight on the top-level forecast: better (lower) WAPE -> more weight
    if total_wape is not None and child_wapes:
        mean_child = float(np.nanmean([w for w in child_wapes if np.isfinite(w)]) or total_wape)
        w_top = float(np.clip(mean_child / (mean_child + total_wape + 1e-9), 0.1, 0.9))
    else:
        w_top = 0.5

    blended_total = w_top * total_path + (1 - w_top) * bu
    children = top_down(blended_total, child_paths)
    # numerical clean-up: force exact coherence
    s = np.sum(children, axis=0)
    fix = blended_total - s
    if children:
        children[int(np.argmax([np.mean(c) for c in children]))] += fix
    return blended_total, [np.clip(c, 0.0, None) for c in children]
