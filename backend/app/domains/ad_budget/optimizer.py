"""Pure budget-reallocation math — no DB, no I/O, fully unit-testable.

Given per-channel spend/revenue/ROAS over a window and a set of guardrails,
produce a new daily budget per channel that shifts money toward the
best-converting channels without violating floors, caps or the max
daily-shift band.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _q(v) -> Decimal:
    if not isinstance(v, Decimal):
        v = Decimal(str(v or 0))
    return v.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class ChannelInput:
    channel_id: str
    platform: str
    name: str
    current_budget: Decimal
    spend: Decimal
    revenue: Decimal
    conversions: int = 0
    roas: Decimal = ZERO
    recent_roas: Optional[Decimal] = None
    min_budget: Optional[Decimal] = None
    max_budget: Optional[Decimal] = None
    is_managed: bool = True
    is_paused: bool = False


@dataclass
class OptimizerConfig:
    total_daily_budget: Optional[Decimal] = None
    target_roas: Decimal = Decimal("2.0")
    kill_roas: Decimal = Decimal("0.7")
    min_channel_share: Decimal = Decimal("0.10")
    max_daily_shift_pct: Decimal = Decimal("0.25")
    aggressiveness: Decimal = Decimal("1.5")
    allow_pause: bool = False
    min_data_conversions: int = 5


@dataclass
class ChannelDecision:
    channel_id: str
    platform: str
    name: str
    before: Decimal
    after: Decimal
    delta: Decimal
    delta_pct: float
    roas: Decimal
    conversions: int
    action: str          # increase | decrease | hold | pause | resume
    reason: str

    def as_dict(self) -> dict:
        return {
            "ad_channel_id": self.channel_id,
            "platform": self.platform,
            "name": self.name,
            "before": float(self.before),
            "after": float(self.after),
            "delta": float(self.delta),
            "delta_pct": self.delta_pct,
            "roas": float(self.roas),
            "conversions": self.conversions,
            "action": self.action,
            "reason": self.reason,
        }


@dataclass
class ReallocationResult:
    decisions: list[ChannelDecision] = field(default_factory=list)
    blended_roas: Decimal = ZERO
    total_before: Decimal = ZERO
    total_after: Decimal = ZERO
    pool: Decimal = ZERO
    noop: bool = False
    note: str = ""

    def as_dicts(self) -> list[dict]:
        return [d.as_dict() for d in self.decisions]


def _effective_roas(ch: ChannelInput) -> Decimal:
    r = ch.roas or ZERO
    if ch.recent_roas is not None:
        return _q(Decimal("0.6") * ch.recent_roas + Decimal("0.4") * r)
    return _q(r)


def optimize(channels: list[ChannelInput], config: OptimizerConfig) -> ReallocationResult:
    blended_spend = sum((c.spend or ZERO for c in channels), ZERO)
    blended_rev = sum((c.revenue or ZERO for c in channels), ZERO)
    blended_roas = _q(blended_rev / blended_spend) if blended_spend > 0 else ZERO

    managed = [c for c in channels if c.is_managed and not c.is_paused]
    fixed = [c for c in channels if not c.is_managed or c.is_paused]

    total_before = sum((_q(c.current_budget) for c in channels), ZERO)

    if not managed:
        return ReallocationResult(
            decisions=[_hold(c, "canal no gestionado por el autopiloto") for c in channels],
            blended_roas=blended_roas, total_before=total_before, total_after=total_before,
            noop=True, note="sin canales gestionados",
        )

    if config.total_daily_budget is not None:
        pool = _q(config.total_daily_budget)
    else:
        pool = sum((_q(c.current_budget) for c in managed), ZERO)

    if pool <= 0:
        return ReallocationResult(
            decisions=[_hold(c, "presupuesto total = 0") for c in channels],
            blended_roas=blended_roas, total_before=total_before, total_after=total_before,
            noop=True, note="pool de presupuesto en cero", pool=pool,
        )

    target = config.target_roas if config.target_roas > 0 else Decimal("1")
    aggr = float(config.aggressiveness or Decimal("1"))

    # --- classify: kill vs active -------------------------------------------
    active: list[ChannelInput] = []
    decisions: list[ChannelDecision] = []
    for c in managed:
        eff = _effective_roas(c)
        enough_data = c.conversions >= config.min_data_conversions
        if config.allow_pause and enough_data and eff < config.kill_roas and c.spend > 0:
            decisions.append(
                ChannelDecision(
                    c.channel_id, c.platform, c.name, _q(c.current_budget), ZERO,
                    _q(-c.current_budget), -100.0, _q(c.roas), c.conversions, "pause",
                    f"ROAS {eff} < umbral de corte {config.kill_roas} con {c.conversions} conv.",
                )
            )
        else:
            active.append(c)

    if not active:
        # everything got paused — nothing to allocate
        for c in fixed:
            decisions.append(_hold(c, "canal fijo"))
        total_after = sum((d.after for d in decisions), ZERO) + sum((_q(c.current_budget) for c in fixed), ZERO)
        return ReallocationResult(
            decisions=decisions, blended_roas=blended_roas, total_before=total_before,
            total_after=_q(total_after), pool=pool, note="todos los canales pausados por ROAS",
        )

    # --- score --------------------------------------------------------------
    scores: dict[str, float] = {}
    for c in active:
        eff = _effective_roas(c)
        if c.conversions < config.min_data_conversions:
            # low confidence: keep near a fair share to gather data
            eff = max(eff, _q(target * Decimal("0.9")))
        ratio = float(max(eff, Decimal("0.05")) / target)
        scores[c.channel_id] = max(ratio, 0.01) ** aggr

    score_sum = sum(scores.values()) or 1.0
    raw = {c.channel_id: pool * Decimal(str(scores[c.channel_id] / score_sum)) for c in active}

    # --- bounds per channel ------------------------------------------------
    lo: dict[str, Decimal] = {}
    hi: dict[str, Decimal] = {}
    shift = config.max_daily_shift_pct
    floor_share = _q(pool * config.min_channel_share)
    for c in active:
        cur = _q(c.current_budget)
        hard_min = _q(c.min_budget) if c.min_budget is not None else ZERO
        hard_max = _q(c.max_budget) if c.max_budget is not None else pool
        if cur > 0:
            band_lo = _q(cur * (Decimal("1") - shift))
            band_hi = _q(cur * (Decimal("1") + shift))
        else:
            band_lo = ZERO
            band_hi = max(floor_share * 2, hard_min)
        l = max(hard_min, band_lo, floor_share if cur > 0 else ZERO)
        h = min(hard_max, band_hi) if band_hi > 0 else hard_max
        if h < l:
            h = l
        lo[c.channel_id] = l
        hi[c.channel_id] = h

    # feasibility: sum(lo) must not exceed pool; if it does, relax floors proportionally
    lo_sum = sum(lo.values(), ZERO)
    if lo_sum > pool:
        scale = pool / lo_sum
        lo = {k: _q(v * scale) for k, v in lo.items()}
        hi = {k: max(hi[k], lo[k]) for k in hi}

    # --- iterative water-fill --------------------------------------------
    alloc = dict(raw)
    fixed_ids: set[str] = set()
    for _ in range(24):
        # clamp
        changed = False
        for cid in list(alloc):
            if cid in fixed_ids:
                continue
            v = alloc[cid]
            if v < lo[cid]:
                alloc[cid] = lo[cid]; fixed_ids.add(cid); changed = True
            elif v > hi[cid]:
                alloc[cid] = hi[cid]; fixed_ids.add(cid); changed = True
        fixed_total = sum((alloc[c] for c in fixed_ids), ZERO)
        free_ids = [c.channel_id for c in active if c.channel_id not in fixed_ids]
        residual = pool - fixed_total
        if not free_ids:
            break
        free_score = sum(scores[c] for c in free_ids) or 1.0
        for cid in free_ids:
            alloc[cid] = _q(residual * Decimal(str(scores[cid] / free_score)))
        if not changed:
            break

    # round + push any residual onto the largest allocation
    alloc = {k: _q(v) for k, v in alloc.items()}
    drift = pool - sum(alloc.values(), ZERO)
    if drift != 0 and alloc:
        biggest = max(alloc, key=lambda k: alloc[k])
        alloc[biggest] = _q(alloc[biggest] + drift)

    # --- build decisions -------------------------------------------------
    for c in active:
        before = _q(c.current_budget)
        after = alloc[c.channel_id]
        delta = _q(after - before)
        pct = float(_q(delta / before * 100)) if before > 0 else (100.0 if after > 0 else 0.0)
        if abs(delta) < CENT:
            action, reason = "hold", f"ROAS {_effective_roas(c)} en objetivo"
        elif delta > 0:
            action = "resume" if before == 0 else "increase"
            reason = f"ROAS {_effective_roas(c)} vs objetivo {target}; +{pct:.0f}%"
        else:
            action = "decrease"
            reason = f"ROAS {_effective_roas(c)} bajo objetivo {target}; {pct:.0f}%"
        if c.conversions < config.min_data_conversions:
            reason += f" (baja confianza: {c.conversions} conv.)"
        decisions.append(
            ChannelDecision(c.channel_id, c.platform, c.name, before, after, delta, pct,
                            _q(c.roas), c.conversions, action, reason)
        )

    for c in fixed:
        decisions.append(_hold(c, "canal fijo / pausado manualmente"))

    total_after = sum((d.after for d in decisions), ZERO)
    return ReallocationResult(
        decisions=decisions,
        blended_roas=blended_roas,
        total_before=total_before,
        total_after=_q(total_after),
        pool=pool,
    )


def _hold(c: ChannelInput, reason: str) -> ChannelDecision:
    b = _q(c.current_budget)
    return ChannelDecision(c.channel_id, c.platform, c.name, b, b, ZERO, 0.0,
                           _q(c.roas), c.conversions, "hold", reason)
